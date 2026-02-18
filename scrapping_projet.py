"""
TITRE : COMPARATEUR DE PRIX DE RECETTES (VERSION PRO)
DESCRIPTION : 
    Script d'automatisation (Bot) qui :
    1. Récupère les données économiques d'une ville (Numbeo).
    2. Cherche des recettes culinaires (Marmiton).
    3. Estime le coût des ingrédients.
    4. Génère un rapport HTML comparatif.

AUTEUR : [Votre Nom/Bot]
DATE : Février 2026
"""

import time
import os
import pathlib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# =============================================================================
# 1. MOTEUR DE NAVIGATEUR (PATTERN: CONTEXT MANAGER)
# =============================================================================
class ScraperEngine:
    """
    Gère le cycle de vie du navigateur Selenium.
    Utilise les méthodes __enter__ et __exit__ pour permettre l'utilisation
    de l'instruction 'with', garantissant la fermeture propre du driver.
    """
    def __init__(self):
        sefl.driver = None

    def __enter__(self):
        """Initialise le navigateur le plus pertinent disponible sur le système."""
       
        # Tentative 1 : Google Chrome (Recommandé, via webdriver_manager)
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--log-level=3") # Réduction de la verbosité des logs
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            print("[INFO] Navigateur Google Chrome initialise avec succes.")
           
        except Exception:
            print("[ATTENTION] Chrome indisponible. Tentative de repli vers un autre navigateur...")
           
            # Tentative 2 : Safari (Natif sous macOS)
            try:
                self.driver = webdriver.Safari()
                print("[INFO] Navigateur Safari initialise avec succes.")
               
            except Exception:
                # Tentative 3 : Firefox (Alternative cross-platform)
                try:
                    self.driver = webdriver.Firefox()
                    print("[INFO] Navigateur Firefox initialise avec succes.")
                   
                except Exception as fatal_error:
                    print("[ERREUR CRITIQUE] Aucun navigateur compatible detecte.")
                    print("--> Action requise (macOS) : Ouvrez le terminal et tapez 'safaridriver --enable'")
                    print("--> Action requise (Windows/Linux) : Installez Google Chrome ou Mozilla Firefox.")
                    raise RuntimeError("Echec de l'initialisation du WebDriver.") from fatal_error

        self.driver.maximize_window()
        return self.driver
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Méthode appelée à la fin du bloc 'with'.
        Ici, on ne ferme pas le driver (pass) pour laisser l'utilisateur voir le résultat.
        Pour fermer automatiquement, on mettrait : self.driver.quit()
        """
        pass 

# =============================================================================
# 2. LOGIQUE MÉTIER : CLASSIFICATION DES INGRÉDIENTS
# =============================================================================
class IngredientClassifier:
    """
    Service statique pour catégoriser un ingrédient brut (ex: '2 tomates')
    dans une famille tarifaire (ex: 'LEGUME').
    """
    
    # Dictionnaire de correspondance : Famille -> Liste de mots-clés
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

    @classmethod
    def identify(cls, name):
        """Parcourt les catégories pour trouver une correspondance dans le nom de l'ingrédient."""
        nom_min = name.lower()
        for fam, mots in cls.CATEGORIES.items():
            for mot in mots:
                if mot in nom_min: return fam
        return "AUTRE" # Catégorie par défaut si rien n'est trouvé

# =============================================================================
# 3. SERVICES DE SCRAPING (DONNÉES EXTERNES)
# =============================================================================
class NumbeoService:
    """Récupère le coût de la vie dans une ville spécifique via Numbeo."""
    
    def __init__(self, driver):
        self.driver = driver
        # Prix par défaut au cas où le scraping échoue ou la ville n'existe pas
        self.base_prices = {
            "base_viande": 15.0, "base_volaille": 10.0, "base_legume": 2.50, 
            "base_feculent": 2.00, "base_laitier": 10.0, "base_fruit": 2.50
        }

    def get_prices(self, city):
        print(f"[INFO] Extraction de l'index des prix pour : {city}...")
        try:
            city_formatted = city.replace(' ', '-').title()
            self.driver.get(f"https://www.numbeo.com/cost-of-living/in/{city_formatted}?displayCurrency=EUR")
           
            # Synchronisation explicite avec le DOM
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CLASS_NAME, "data_wide_table")))
           
            rows = self.driver.find_elements(By.TAG_NAME, "tr")
            for row in rows: self._parse(row)
        except:
            print("[ATTENTION] Site inaccessible ou ville introuvable. Utilisation des tarifs par defaut.")
        return self.base_prices

    def _parse(self, row):
        """Analyse une ligne HTML du tableau Numbeo pour extraire le prix."""
        try:
            txt = row.text
            # Extraction et conversion du prix (nettoyage du symbole €)
            val = float(row.find_element(By.CLASS_NAME, "priceValue").text.replace("€", "").replace(",", "").strip())
            
            # Mise à jour des prix de base selon le contenu de la ligne
            if "Chicken" in txt: self.base_prices["base_volaille"] = val
            elif "Beef" in txt: self.base_prices["base_viande"] = val
            elif "Rice" in txt: self.base_prices["base_feculent"] = val
            elif "Cheese" in txt: self.base_prices["base_laitier"] = val
            # Moyenne pour les légumes courants
            elif any(x in txt for x in ["Tomato", "Potato", "Onion"]): 
                self.base_prices["base_legume"] = (self.base_prices["base_legume"] + val) / 2
        except: pass

class MarmitonService:
    """Gère la recherche et l'extraction de recettes sur Marmiton."""
    
    def __init__(self, driver):
        self.driver = driver

    def search_recipes(self, query):
        print(f"[INFO] Recherche des recettes pour : '{query}'...")
        self.driver.get(f"https://www.marmiton.org/recettes/recherche.aspx?aqt={query}&st=1")
        self._cookies() # Gestion de la popup RGPD
        
        recettes = []
        try:
            time.sleep(2) # Pause pour laisser le JS s'exécuter
            
            # Recherche des liens via XPath (plus robuste que les classes CSS changeantes)
            liens = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/recettes/recette_')]")
            
            for lien in liens:
                if len(recettes) >= 3: break # Limite à 3 résultats
                r = self._info(lien)
                # Évite les doublons
                if r and r['nom'] not in [x['nom'] for x in recettes]:
                    recettes.append(r)
        except: pass
        return recettes

    def get_ingredients(self, url):
        """Extrait la liste des ingrédients d'une page recette spécifique."""
        self.driver.get(url)
        try:
            # Scroll nécessaire car certains sites chargent le contenu en "Lazy Loading"
            self.driver.execute_script("window.scrollTo(0, 600);")
            time.sleep(1) 
            
            # Tentative de récupération avec la classe standard
            items = self.driver.find_elements(By.CLASS_NAME, "card-ingredient-title")
            # Fallback (Plan B) si la classe standard ne fonctionne pas
            if not items: items = self.driver.find_elements(By.XPATH, "//span[contains(@class, 'ingredient-name')]")
            
            return [item.text.strip() for item in items if item.text.strip()]
        except: return []

    def _cookies(self):
        """Ferme la bannière de cookies si elle apparaît."""
        try: 
            WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))).click()
        except: pass

    def _info(self, el):
        """Extrait le titre et l'URL d'un élément Web recette."""
        try:
            url = el.get_attribute("href")
            # Parfois le titre est dans un h4, parfois c'est le texte du lien
            nom = el.text.strip() or el.find_element(By.TAG_NAME, "h4").text.strip()
            if nom and url and len(nom)>5: return {"nom": nom, "url": url}
        except: pass
        return None

# =============================================================================
# 4. MOTEUR DE CALCUL (ESTIMATION)
# =============================================================================
class CostCalculator:
    """Calcule le coût estimatif d'une recette basé sur les prix Numbeo."""
    
    def __init__(self, prices):
        self.prices = prices
        self.total = 0.0

    def calculate(self, ingredients):
        self.total = 0.0
        details = []
        for ing in ingredients:
            fam = IngredientClassifier.identify(ing)
            cost = self._cost(fam)
            self.total += cost
            details.append({"Ing": ing, "Cost": cost})
        return self.total, details

    def _cost(self, fam):
        """
        Applique une règle métier heuristique : 
        Prix unitaire = Prix au kilo (Numbeo) * Quantité estimée moyenne
        """
        p = self.prices
        # Les multiplicateurs (ex: 0.15) correspondent à une portion estimée (ex: 150g)
        mapping = {
            "VIANDE_ROUGE": p["base_viande"]*0.15, 
            "VOLAILLE": p["base_volaille"]*0.15,
            "POISSON": p["base_viande"]*1.2*0.15, 
            "LEGUME": p["base_legume"]*0.15,
            "FECULENT": p["base_feculent"]*0.1, 
            "LAITIER": p["base_laitier"]*0.05,
            "EPICERIE_SUCREE": 0.2, # Prix forfaitaire
            "CONDIMENT": 0.1, 
            "AROMATE": 0.3
        }
        return mapping.get(fam, 0.5) # 0.50€ par défaut pour "AUTRE"

# =============================================================================
# 5. GÉNÉRATEUR DE RAPPORT (DASHBOARD HTML)
# =============================================================================
class DashboardGenerator:
    """Génère un fichier HTML visuel pour comparer les résultats."""
    
    @staticmethod
    def create_comparison(results, city, dish_name):
        if not results: return
        
        # Identification de la recette la moins chère
        winner = min(results, key=lambda x: x['total'])
        
        cards_html = ""
        for r in results:
            is_winner = (r == winner)
            
            # Application de styles CSS spécifiques pour le gagnant
            border_style = "4px solid #27ae60" if is_winner else "1px solid #ddd"
            bg_color = "#f0fff4" if is_winner else "#fff"
            badge = '<div class="badge">MEILLEUR PRIX</div>' if is_winner else ""
            
            # Formatage de la liste d'ingrédients (tronquée à 6 éléments)
            ing_html = "".join([f"<li>{d['Ing']}</li>" for d in r['details'][:6]])
            if len(r['details']) > 6: ing_html += "<li>...</li>"

            # Construction de la "Carte" HTML pour une recette
            cards_html += f"""
            <div class="card" style="border: {border_style}; background: {bg_color}">
                {badge}
                <h3>{r['nom']}</h3>
                <div class="price">{r['total']:.2f} €</div>
                <div class="ing-list">
                    <strong>Ingredients cles :</strong>
                    <ul>{ing_html}</ul>
                </div>
                <a href="{r['url']}" target="_blank" class="btn">Voir la recette sur Marmiton</a>
            </div>
            """

        # Gabarit HTML complet avec CSS intégré
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Comparateur {dish_name}</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f7f6; padding: 40px; color: #333; }}
                h1 {{ text-align: center; color: #2c3e50; margin-bottom: 10px; }}
                .subtitle {{ text-align: center; color: #7f8c8d; margin-bottom: 40px; }}
                .container {{ display: flex; flex-wrap: wrap; justify-content: center; gap: 30px; }}
                .card {{ background: white; width: 320px; padding: 25px; border-radius: 15px; box-shadow: 0 10px 20px rgba(0,0,0,0.08); position: relative; transition: transform 0.3s; display: flex; flex-direction: column; justify-content: space-between; }}
                .card:hover {{ transform: translateY(-5px); }}
                .badge {{ position: absolute; top: -15px; right: -10px; background: #27ae60; color: white; padding: 8px 15px; border-radius: 20px; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.2); font-size: 0.9em; }}
                h3 {{ font-size: 1.1em; height: 50px; overflow: hidden; }}
                .price {{ font-size: 2.8em; font-weight: 800; color: #2c3e50; margin: 15px 0; text-align: center; }}
                .ing-list {{ font-size: 0.85em; color: #666; margin-bottom: 20px; }}
                ul {{ padding-left: 20px; }}
                .btn {{ display: block; text-align: center; background: #3498db; color: white; text-decoration: none; padding: 12px; border-radius: 8px; font-weight: bold; transition: background 0.2s; }}
                .btn:hover {{ background: #2980b9; }}
                .footer {{ text-align: center; margin-top: 50px; font-size: 0.8em; color: #aaa; }}
            </style>
        </head>
        <body>
            <h1>COMPARATEUR DE PRIX</h1>
            <div class="subtitle">Analyse pour : <strong>{dish_name.upper()}</strong> a <strong>{city.upper()}</strong></div>
            
            <div class="container">
                {cards_html}
            </div>

            <div class="footer">
                Genere automatiquement par Python - Prix bases sur Numbeo - Recettes via Marmiton
            </div>
        </body>
        </html>
        """
        
        # Sauvegarde du fichier
        filename = f"comparatif_{dish_name.replace(' ', '_')}.html"
        path = os.path.abspath(filename)
        with open(path, "w", encoding="utf-8") as f: f.write(html)
        return path

        
        # --- CORRECTION CHEMIN MAC/WINDOWS (SAUVEGARDE BUREAU) ---
        filename = f"comparatif_{dish_name.replace(' ', '_')}.html"
       
        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        # Fallback au cas où le dossier "Desktop" serait introuvable
        if not os.path.exists(desktop_dir):
            desktop_dir = os.path.expanduser("~")
           
        path = os.path.join(desktop_dir, filename)
       
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
           
        return path
# =============================================================================
# 6. POINT D'ENTRÉE PRINCIPAL
# =============================================================================
def main():
    print("\n" + "="*40)
    print("   COMPARATEUR DE PRIX DE RECETTES")
    print("="*40 + "\n")

    # 1. Interactions utilisateur (Entrées)
    ville = input(">> Dans quelle ville faites-vous vos courses ? (ex: Paris, Lyon) : ")
    plat = input(">> Quel plat voulez-vous cuisiner ? (ex: Lasagnes, Quiche) : ")

    if not ville or not plat:
        print("[ERREUR] Veuillez entrer une ville et un plat.")
        return

    print("\n[INFO] Lancement du robot...")

    # Utilisation du ScraperEngine avec 'with' pour garantir la fermeture
    with ScraperEngine() as driver:
        
        # 2. Récupération des données économiques
        numbeo = NumbeoService(driver)
        prices = numbeo.get_prices(ville)

        # 3. Recherche des recettes
        marmiton = MarmitonService(driver)
        recettes = marmiton.search_recipes(plat)

        if not recettes:
            print(f"[ERREUR] Aucune recette trouvée pour '{plat}'.")
            return

        # 4. Analyse et calculs
        results = []
        calc = CostCalculator(prices)

        print(f"\n[INFO] Comparaison de {len(recettes)} recettes en cours...")
        
        for i, r in enumerate(recettes):
            print(f"   [{i+1}/{len(recettes)}] Analyse : {r['nom']}...")
            ing = marmiton.get_ingredients(r['url'])
            total, details = calc.calculate(ing)
            
            results.append({
                "nom": r['nom'],
                "url": r['url'],
                "total": total,
                "details": details
            })

        # 5. Génération du rapport
        print("\n[INFO] Creation du rapport visuel...")
        path = DashboardGenerator.create_comparison(results, ville, plat)
        
        print(f"[SUCCES] Termine ! Affichage des resultats via le navigateur...")
       
        # Structuration de l'URI universelle (Format OS agnostique - Windows/macOS/Linux)
        file_uri = pathlib.Path(path).as_uri()
        driver.get(file_uri)
       
        input("\nMaintenez une touche pour interrompre l'execution et fermer l'instance...")

if __name__ == "__main__":
    main()
