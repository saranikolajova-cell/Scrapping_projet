import polars as pl
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

CATEGORIES = {
    "VIANDE_ROUGE": ["boeuf", "bœuf", "steak", "porc", "lard", "jambon", "saucisse", "veau", "agneau"],
    "VOLAILLE": ["poulet", "dinde", "canard", "volaille"],
    "LEGUME": ["tomate", "oignon", "carotte", "courgette", "aubergine", "poivron", "ail", "pomme de terre", "champignon", "patate"],
    "FECULENT": ["riz", "pâte", "spaghetti", "blé", "semoule", "pain", "pate"],
    "LAITIER": ["lait", "crème", "beurre", "yaourt", "fromage", "gruyère"]
}

def get_numbeo_prices(driver, city):
    city_url = city.replace(" ", "-")
    driver.get(f"https://www.numbeo.com/cost-of-living/in/{city_url}?displayCurrency=EUR")
    prix_ref = {"base_viande": 15.0, "base_volaille": 10.0, "base_legume": 2.50, "base_feculent": 2.00, "base_laitier": 10.0}
    try:
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "data_wide_table")))
        rows = driver.find_elements(By.TAG_NAME, "tr")
        for row in rows:
            text = row.text
            try:
                element_prix = row.find_element(By.CLASS_NAME, "priceValue")
                val = float(element_prix.text.replace("€", "").replace(",", ".").strip())
                if "Chicken" in text: prix_ref["base_volaille"] = val
                elif "Beef" in text: prix_ref["base_viande"] = val
                elif "Rice" in text: prix_ref["base_feculent"] = val
                elif "Cheese" in text: prix_ref["base_laitier"] = val
            except: continue
    except: pass
    return prix_ref

def get_clean_recipes(driver, limit=8):
    recettes = []
    # Methode 1 : Par ID recipe-X
    for i in range(1, limit + 1):
        try:
            container = driver.find_element(By.ID, f"recipe-{i}")
            a_tag = container.find_element(By.TAG_NAME, "a")
            nom = a_tag.text.strip()
            if nom:
                recettes.append({"nom": nom, "element": a_tag})
        except: continue
    
    # Methode 2 : Si la liste est vide, on cherche par classe de titre
    if not recettes:
        elements = driver.find_elements(By.CLASS_NAME, "mrtn-recipe-card__title")
        for el in elements[:limit]:
            try:
                a_tag = el.find_element(By.TAG_NAME, "a")
                nom = a_tag.text.strip()
                if nom:
                    recettes.append({"nom": nom, "element": a_tag})
            except: continue
    return recettes

if __name__ == "__main__":
    ville = input("Ville : ")
    driver = webdriver.Safari()
    driver.maximize_window()
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("https://www.marmiton.org/qu-est-ce-qu-on-mange-ce-soir-sc29.html")
        
        try:
            cookie = wait.until(EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button")))
            cookie.click()
        except: pass

        time.sleep(5) # Attente pour le chargement complet
        mes_recettes = get_clean_recipes(driver)

        print("\n--- RECETTES TROUVEES ---")
        if not mes_recettes:
            print("Aucune recette detectee.")
        else:
            for i, r in enumerate(mes_recettes):
                print(f"{i+1}. {r['nom']}")

            index = int(input(f"\nChoix (1-{len(mes_recettes)}) : ")) - 1
            choix = mes_recettes[index]

            print(f"Analyse de : {choix['nom']}")
            driver.execute_script("arguments[0].click();", choix['element'])
            
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "card-ingredient-title")))
            items = driver.find_elements(By.CLASS_NAME, "card-ingredient-title")
            liste_ing = [it.text.strip() for it in items]

            prix_marche = get_numbeo_prices(driver, ville)
            
            final_data = []
            total = 0.0

            for ing in liste_ing:
                famille = "AUTRE"
                for f, mots in CATEGORIES.items():
                    if any(m in ing.lower() for m in mots):
                        famille = f
                        break
                p = 0.50 
                if famille == "VIANDE_ROUGE": p = prix_marche["base_viande"] * 0.15
                elif famille == "VOLAILLE": p = prix_marche["base_volaille"] * 0.15
                elif famille == "LEGUME": p = prix_marche["base_legume"] * 0.15
                elif famille == "FECULENT": p = prix_marche["base_feculent"] * 0.10
                elif famille == "LAITIER": p = prix_marche["base_laitier"] * 0.05
                total += p
                final_data.append({"Ingrédient": ing, "Prix": round(p, 2)})

            print("\n", pl.DataFrame(final_data))
            print(f"\nTOTAL ESTIMÉ : {total:.2f} EUR")

    except Exception as e:
        print(f"Erreur : {e}")

    finally:
        input("\nEntrée pour fermer...")
        driver.quit()