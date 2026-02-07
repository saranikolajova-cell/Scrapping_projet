"""
TITRE : ESTIMATEUR DE COÛT DE REPAS AUTOMATISÉ
DESCRIPTION : Ce script croise des données économiques avec des recettes populaires.
"""

import time
import polars as pl
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 1. BASE DE CONNAISSANCES ---
CATEGORIES = {
    "VIANDE_ROUGE": ["boeuf", "bœuf", "steak", "porc", "lard", "jambon", "saucisse", "veau", "agneau", "chorizo", "merguez", "viande", "bacon", "lardon"],
    "VOLAILLE": ["poulet", "dinde", "canard", "oie", "volaille", "chapon", "cuisse", "blanc de"],
    "POISSON": ["poisson", "saumon", "thon", "crevette", "moule", "cabillaud", "fruit de mer", "calamar", "truite"],
    "LEGUME": ["tomate", "oignon", "carotte", "courgette", "aubergine", "poivron", "ail", "échalote", "echalote", "champignon", "salade", "épinard", "haricot", "pois", "pomme de terre", "patate", "chou", "poireau", "avocat", "concombre"],
    "FRUIT": ["pomme", "poire", "banane", "citron", "orange", "fraise", "framboise", "ananas", "fruit", "zeste"],
    "FECULENT": ["riz", "pâte", "spaghetti", "nouille", "blé", "semoule", "quinoa", "pain", "baguette", "toast", "farine", "galette", "tortilla"],
    "LAITIER": ["lait", "crème", "beurre", "yaourt", "fromage", "gruyère", "parmesan", "mozzarella", "comté", "cheddar", "emmental"],
    "EPICERIE_SUCREE": ["sucre", "miel", "sirop", "chocolat", "cacao", "confiture", "maïzena", "levure", "vanille"],
    "CONDIMENT": ["sel", "poivre", "huile", "vinaigre", "sauce", "soja", "moutarde", "ketchup", "mayonnaise", "cube", "bouillon", "vin", "alcool", "rhum", "eau"],
    "AROMATE": ["gingembre", "persil", "basilic", "thym", "laurier", "coriandre", "menthe", "épice", "curry", "paprika", "cumin", "cannelle", "herbe", "piment", "quatre-épices", "origan"]
}

# --- 2. MODULES DE SCRAPING ---

def get_numbeo_prices(driver, city):
    """Récupère les prix moyens locaux sur Numbeo."""
    print(f"Connexion à Numbeo pour : {city}...")
    city_url = city.replace(" ", "-").title() 
    driver.get(f"https://www.numbeo.com/cost-of-living/in/{city_url}?displayCurrency=EUR")
    
    prix_ref = {
        "base_viande": 15.0, "base_volaille": 10.0, "base_legume": 2.50,
        "base_feculent": 2.00, "base_laitier": 10.0, "base_fruit": 2.50
    }
    
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "data_wide_table")))
        rows = driver.find_elements(By.TAG_NAME, "tr")
        for row in rows:
            text = row.text
            try:
                element_prix = row.find_element(By.CLASS_NAME, "priceValue")
                val = float(element_prix.text.replace("€", "").replace(",", "").strip())
                
                if "Chicken" in text: prix_ref["base_volaille"] = val
                elif "Beef" in text: prix_ref["base_viande"] = val
                elif "Rice" in text: prix_ref["base_feculent"] = val
                elif "Cheese" in text: prix_ref["base_laitier"] = val
                elif "Apple" in text or "Orange" in text: prix_ref["base_fruit"] = val
                elif "Tomato" in text or "Potato" in text or "Onion" in text: 
                    prix_ref["base_legume"] = (prix_ref["base_legume"] + val) / 2
            except: continue
        print("Données économiques locales récupérées.")
    except:
        print("Utilisation des prix par défaut (Numbeo inaccessible).")
    
    return prix_ref

def get_marmiton_suggestions(driver):
    """
    Récupère une liste de recettes via une recherche générique 'Plat principal'.
    Cette méthode est plus robuste que la page d'accueil.
    """
    print("Recherche des recettes populaires...")
    # On lance une recherche explicite pour être sûr d'avoir des résultats
    driver.get("https://www.marmiton.org/recettes/recherche.aspx?aqt=plat&st=1")
    
    try:
        wait = WebDriverWait(driver, 5)
        cookie = wait.until(EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button")))
        cookie.click()
    except: pass
    
    recettes = []
    try:
        time.sleep(3) 
        # STRATÉGIE DE SCRAPING UNIVERSELLE :
        # On cherche tous les liens <a> qui contiennent "/recettes/recette_" dans leur URL.
        # Cela évite de dépendre d'une classe CSS qui change.
        liens = driver.find_elements(By.XPATH, "//a[contains(@href, '/recettes/recette_')]")
        
        for lien in liens:
            try:
                # On cherche le titre (souvent dans un h4 ou h3 à l'intérieur du lien)
                # On tente h4 d'abord, sinon on prend tout le texte
                try:
                    nom = lien.find_element(By.TAG_NAME, "h4").text.strip()
                except:
                    nom = lien.text.strip()
                
                url = lien.get_attribute("href")
                
                # Filtrage : On évite les doublons et les titres vides/bizarres
                if nom and url and len(nom) > 5 and nom not in [r['nom'] for r in recettes]:
                    recettes.append({"nom": nom, "url": url})
                
                if len(recettes) >= 10: break # On s'arrête à 10 recettes
            except: continue
            
    except Exception as e:
        print(f"Erreur technique récupération recettes : {e}")
        
    return recettes

def get_recipe_details(driver, url):
    """Extrait les ingrédients d'une page recette."""
    print(f"Analyse des ingrédients...")
    driver.get(url)
    
    ingredients = []
    try:
        driver.execute_script("window.scrollTo(0, 600);")
        time.sleep(2)
        
        # On cherche les titres des ingrédients
        items = driver.find_elements(By.CLASS_NAME, "card-ingredient-title")
        
        # Si la méthode 1 échoue, on tente une méthode plus large (certaines pages Marmiton sont différentes)
        if len(items) == 0:
             items = driver.find_elements(By.XPATH, "//span[contains(@class, 'ingredient-name')]")

        for item in items:
            nom = item.text.strip()
            if nom: ingredients.append(nom)
            
    except:
        print("Erreur lecture ingrédients.")
        
    return ingredients

def identifier_famille(nom_ingredient):
    """Classification des ingrédients."""
    nom_min = nom_ingredient.lower()
    for famille, mots_cles in CATEGORIES.items():
        for mot in mots_cles:
            if mot in nom_min:
                return famille
    return "AUTRE"

# --- 3. EXÉCUTION ---

if __name__ == "__main__":
    ville = input("Ville pour l'index économique (ex: Paris) : ")

    options = webdriver.ChromeOptions()
    options.add_argument("--log-level=3")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()

    try:
        # ÉTAPE 1 : Prix
        prix_marche = get_numbeo_prices(driver, ville)

        # ÉTAPE 2 : Menu
        mes_recettes = get_marmiton_suggestions(driver)

        if not mes_recettes:
            print("Aucune recette trouvée. Le site a peut-être changé de structure.")
        else:
            print("\n--- SÉLECTION DU MENU ---")
            for i, r in enumerate(mes_recettes):
                print(f"{i+1}. {r['nom']}")
            
            while True:
                try:
                    choix_index = int(input(f"\nNuméro de la recette (1-{len(mes_recettes)}) : ")) - 1
                    if 0 <= choix_index < len(mes_recettes):
                        recette_choisie = mes_recettes[choix_index]
                        break
                except: pass
            
            print(f"\n Traitement de : {recette_choisie['nom']}")
            
            # ÉTAPE 3 : Ingrédients
            liste_ingredients = get_recipe_details(driver, recette_choisie['url'])
            
            # ÉTAPE 4 : Calcul
            final_data = []
            total_estime = 0.0
            
            for ing in liste_ingredients:
                famille = identifier_famille(ing)
                prix = 0.0
                infos = ""

                if famille == "VIANDE_ROUGE":
                    prix = prix_marche["base_viande"] * 0.150
                    infos = "Viande (~150g)"
                elif famille == "VOLAILLE":
                    prix = prix_marche["base_volaille"] * 0.150
                    infos = "Volaille (~150g)"
                elif famille == "POISSON":
                    prix = prix_marche["base_viande"] * 1.2 * 0.150
                    infos = "Poisson (Est.)"
                elif famille == "LEGUME":
                    prix = prix_marche["base_legume"] * 0.150
                    infos = "Légumes frais"
                elif famille == "FECULENT":
                    prix = prix_marche["base_feculent"] * 0.100
                    infos = "Riz/Pâtes (~100g)"
                elif famille == "LAITIER":
                    prix = prix_marche["base_laitier"] * 0.050
                    infos = "Fromage/Beurre"
                elif famille == "EPICERIE_SUCREE":
                    prix = 0.20
                    infos = "Forfait Épicerie"
                elif famille == "CONDIMENT":
                    prix = 0.10
                    infos = "Forfait Sel/Huile"
                elif famille == "AROMATE":
                    prix = 0.30
                    infos = "Herbes fraiches"
                else:
                    prix = 0.50
                    infos = "Divers"

                total_estime += prix
                final_data.append({
                    "Ingrédient": ing,
                    "Famille": famille,
                    "Type": infos,
                    "Coût (€)": round(prix, 2)
                })

            df = pl.DataFrame(final_data)
            print("\n", df)
            print("="*50)
            print(f"💰 COÛT ESTIMÉ DU REPAS ({ville}) : {total_estime:.2f} €")
            print("="*50)

    except Exception as e:
        print(f"Erreur globale : {e}")

    finally:
        driver.quit()


    except Exception as e:
        print(f"Erreur : {e}")

    finally:
        input("\nEntrée pour fermer...")
        driver.quit()
