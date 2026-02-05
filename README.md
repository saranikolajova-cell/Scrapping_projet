# AUTOMATED FOOD COST ESTIMATOR (AFCE)

## DESCRIPTION DU PROJET

Ce projet est un outil d'automatisation développé en Python conçu pour estimer le coût de revient d'un repas fait maison en fonction de la localisation géographique de l'utilisateur.

L'application croise dynamiquement deux sources de données hétérogènes :
1.  **Marmiton.org** : Extraction structurée des ingrédients et des quantités d'une recette culinaire.
2.  **Numbeo.com** : Récupération en temps réel des indices du coût de la vie (prix des denrées alimentaires) pour une ville spécifique.

L'objectif est de fournir une estimation financière précise en appliquant les prix du marché local aux ingrédients nécessaires, grâce à un algorithme de classification sémantique.

---

## ARCHITECTURE TECHNIQUE & PRÉREQUIS

Ce programme est optimisé pour un environnement Windows utilisant le navigateur Google Chrome.

### Stack Technologique et Justification des Packages

Le projet repose sur un environnement Python standard. Le choix des bibliothèques est justifié par des contraintes techniques spécifiques :

| Package | Rôle Technique & Utilité Critique |
| :--- | :--- |
| **selenium** | **Moteur d'Automatisation Web.** Contrairement aux bibliothèques de requêtes HTTP classiques, Selenium permet de piloter une instance réelle de navigateur. Il est indispensable pour ce projet afin de gérer le rendu JavaScript dynamique (scroll infini sur Marmiton, chargement asynchrone des tableaux sur Numbeo) et l'interaction utilisateur (gestion des bannières de consentement). |
| **webdriver-manager** | **Gestionnaire de Pilotes.** Cette bibliothèque assure la stabilité du déploiement. Elle détecte la version locale de Google Chrome et télécharge/installe automatiquement le binaire `chromedriver.exe` correspondant. Cela élimine les erreurs de compatibilité et de configuration du PATH. |
| **polars** | **Traitement de Données Haute Performance.** Sélectionné comme alternative moderne à Pandas. Polars est utilisé pour structurer les données extraites (ingrédients, catégories, prix, calculs) et générer un rendu tabulaire propre et lisible dans le terminal. Il offre une gestion optimisée de la mémoire. |

---

## INSTALLATION ET CONFIGURATION

Pour garantir le bon fonctionnement des dépendances, l'exécution doit se faire dans un environnement virtuel.

### 1. Préparation du Répertoire
Placez-vous dans le dossier de votre projet via votre terminal :
```bash
cd Documents/Programmation
### 2. Création de l'Environnement Virtuel
Créez un environnement isolé (nommé ici name) pour installer les paquets sans conflit système :

Bash
python -m venv name
### 3. Activation de l'Environnement (Étape Critique)
L'activation est nécessaire à chaque nouvelle session de travail.

Sur Windows (PowerShell) :

PowerShell
.\name\Scripts\activate
Sur macOS / Linux :

Bash
source name/bin/activate
(L'indicateur (name) doit apparaître au début de votre ligne de commande).

### 4. Installation des Dépendances
Installez les bibliothèques requises via le gestionnaire de paquets pip :

Bash
pip install selenium webdriver-manager polars
GUIDE D'UTILISATION
Une fois l'environnement activé, exécutez le script principal :

Bash
python main.py
Scénario d'Exécution
Le programme demandera deux informations dans le terminal :

Ville cible : Entrez le nom d'une ville majeure (ex: Paris, Lyon, London). Le script calibrera les prix selon cette localité.

URL de la recette : Collez l'URL complète d'une recette Marmiton (ex: https://www.marmiton.org/recettes/...).

## Exemple de Sortie (Terminal)
Plaintext
--- RAPPORT FINANCIER : PARIS ---
shape: (5, 4)
┌──────────────┬──────────────┬───────────────────────────┬───────────────┐
│ Ingrédient   ┆ Catégorie    ┆ Base de Calcul            ┆ Coût Est. (€) │
│ ---          ┆ ---          ┆ ---                       ┆ ---           │
│ str          ┆ str          ┆ str                       ┆ f64           │
╞══════════════╪══════════════╪═══════════════════════════╪═══════════════╡
│ Filet Mignon ┆ VIANDE_ROUGE ┆ Viande (Index: Boeuf)     ┆ 3.85          │
│ Oignons      ┆ LEGUME       ┆ Légume (Moyenne locale)   ┆ 0.30          │
│ Riz Basmati  ┆ FECULENT     ┆ Féculent (Index: Riz)     ┆ 0.20          │
└──────────────┴──────────────┴───────────────────────────┴───────────────┘
==================================================
COÛT TOTAL ESTIMÉ DU REPAS : 4.35 €
==================================================

### LOGIQUE ALGORITHMIQUE
Le programme utilise une méthode de Classification Sémantique pour estimer les coûts :

Extraction : Le script isole les ingrédients bruts.

Mapping : Il compare chaque ingrédient à un dictionnaire interne (CATEGORIES) contenant des listes de mots-clés.

Exemple : "Lardon" est identifié comme appartenant à la famille VIANDE_ROUGE.

Tarification : Il applique le prix moyen de la famille (récupéré sur Numbeo) à la quantité estimée. Si un ingrédient est inconnu, un coût forfaitaire de sécurité est appliqué.

AVERTISSEMENT
Ce projet est réalisé à des fins pédagogiques.

Respect des sites : L'automatisation inclut des délais d'attente pour ne pas surcharger les serveurs cibles.

Données : Les informations extraites ne sont pas stockées de manière persistante ni utilisées à des fins commerciales.
Données : Les informations extraites ne sont pas stockées de manière persistante ni utilisées à des fins commerciales.

NIKOLAJOVA Sara, TISNES Francesca - M1 APE - SE / DS2E - Université de Strasbourg
