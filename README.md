# AUTOMATED FOOD COST ESTIMATOR (AFCE) - Multiplatform 

## Description du Projet

L'Automated Food Cost Estimator (AFCE) est un outil d'automatisation (Web Scraping) développé en Python. Il permet d'estimer le coût de revient d'un repas fait maison en croisant dynamiquement les recettes populaires avec le coût de la vie local de l'utilisateur.

L'application interroge deux sources de données :
1. **Marmiton.org** : Recherche d'un plat cible, sélection des 3 meilleures recettes et extraction structurée de leurs listes d'ingrédients.
2. **Numbeo.com** : Récupération en temps réel des indices du coût de la vie (prix au kilo/litre des denrées alimentaires) pour une ville spécifique.

Le résultat est généré sous la forme d'un **Dashboard HTML interactif et local**, permettant de comparer visuellement les options et d'identifier le meilleur rapport qualité/prix.

---

## Architecture Technique & Logique Algorithmique

Ce programme repose sur une architecture Orientée Objet (POO) favorisant la modularité et la maintenabilité.

### Flux de traitement
1. **Moteur Multi-Navigateur (`ScraperEngine`)** : Gère l'instance Selenium via un *Context Manager* (`with`). Il implémente un système de repli (fallback) automatique : il tente d'abord d'utiliser Google Chrome, puis Safari (macOS), et enfin Firefox.
2. **Classification Sémantique (`IngredientClassifier`)** : Un algorithme analyse la chaîne de caractères brute de chaque ingrédient et l'associe à une catégorie tarifaire mère (ex: "VIANDE_ROUGE", "LEGUME", "FECULENT") via une recherche de mots-clés.
3. **Heuristique de Tarification (`CostCalculator`)** : Applique un multiplicateur de portion moyenne au prix brut récupéré sur Numbeo pour estimer le coût réel de l'ingrédient dans la recette.
4. **Génération Agnostique (`DashboardGenerator` & `pathlib`)** : Crée un rapport HTML stylisé. Le module natif `pathlib` garantit que l'URI du fichier généré est formatée correctement quel que soit le système d'exploitation (Windows, macOS ou Linux).

### Stack Technologique et Dépendances

| Package | Rôle Technique & Utilité Critique |
| :--- | :--- |
| **selenium** | **Moteur d'Automatisation Web.** Indispensable pour piloter une instance de navigateur réelle, gérer le rendu JavaScript dynamique (lazy-loading) et interagir avec le DOM (gestion des modales RGPD). |
| **webdriver-manager** | **Gestionnaire de Pilotes.** Détecte l'environnement OS et télécharge automatiquement le binaire compatible (ex: `chromedriver`). Élimine les erreurs de variables d'environnement (PATH) et garantit la portabilité du code. |

---

## Installation et Configuration

Pour garantir le bon fonctionnement des dépendances et isoler l'environnement d'exécution, il est fortement recommandé d'utiliser un environnement virtuel.

### 1. Préparation du Répertoire
Clonez le dépôt et placez-vous dans le dossier du projet via votre terminal :
```bash
git clone <url-du-repo>
cd nom-du-repo
```

### 2. Création de l'Environnement Virtuel
Créez un environnement isolé (nommé venv) :
```bash
python -m venv venv
```

### 3. Activation de l'Environnement
L'activation est requise à chaque nouvelle session de terminal.
Sur Windows (PowerShell) :
```powerShell
.\venv\Scripts\activate
```
Sur macOS / Linux :
```bash
source venv/bin/activate
```

### 4. Installation des Dépendances
Installez les bibliothèques requises via le gestionnaire de paquets pip :
```bash
pip install selenium webdriver-manager 
```
### 5. Cas Particulier : Utilisateurs macOS avec Safari
Si Google Chrome n'est pas installé sur votre Mac, le script basculera automatiquement sur Safari. Pour autoriser l'automatisation, vous devez exécuter cette commande une seule fois dans votre terminal système :
```bash
safaridriver --enable
```
---
## Guide d'Utilisation
Une fois l'environnement activé, lancez le script principal :
```bash
python main.py
```
### Scénario d'Exécution
Le programme fonctionne en mode interactif dans le terminal et requiert deux paramètres :

Ville de référence : Saisissez une ville majeure (ex: Paris, Lyon, Bruxelles). Le script calibrera la tarification sur cette base.

Plat à analyser : Saisissez le nom générique d'une recette (ex: Lasagnes, Quiche lorraine).

Le script se chargera du scraping en arrière-plan (sans action requise de votre part) et ouvrira automatiquement le navigateur web par défaut à la fin du processus pour afficher le fichier comparatif_NomDuPlat.html.
---
## Avertissements et Considérations Légales
Usage Pédagogique : Ce projet est une démonstration technique (Proof of Concept) visant à illustrer l'architecture logicielle, la POO en Python et l'automatisation web.

Respect de la charge serveur : Le code intègre des temporisations (time.sleep) pour limiter la fréquence des requêtes HTTP et respecter l'intégrité des serveurs cibles (Marmiton, Numbeo).

Confidentialité : Les données extraites sont éphémères. Elles servent uniquement au calcul en cours d'exécution et à la génération du rapport HTML local. Aucune base de données persistante n'est alimentée à des fins commerciales.
---

NIKOLAJOVA Sara, TISNES Francesca - M1 APE - SE / DS2E - Université de Strasbourg
