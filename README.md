# Telecom Customer Churn Prediction

Application web de prédiction du désabonnement des clients télécoms, développée avec Python, Flask et un modèle Random Forest.

Deux interfaces sont accessibles dans la même application : **Predict Single Customer** pour un client et **Predict from CSV/Excel** pour un fichier clients.

![Interface de l’application](static/images/interface.jpg)

## Interface 1 — Prédiction individuelle

Le bouton **Predict Single Customer** ouvre un formulaire organisé en trois parties :

- **Profil et contrat** : statut senior, personnes à charge, ancienneté et type de contrat.
- **Services Internet** : sécurité, sauvegarde, protection des appareils et assistance technique.
- **Facturation** : charges mensuelles et charges totales.

Après un clic sur **Predict**, le résultat affiche la classe prédite — `Churn predicted` ou `Not Churn predicted` — et un rappel des informations saisies.

## Interface 2 — Prédiction par fichier CSV / Excel

Le bouton **Predict from CSV/Excel** permet de charger plusieurs clients en une seule opération.

1. Choisir un fichier CSV ou Excel `.xlsx`.
2. Cliquer sur **Predict**.
3. Consulter la synthèse et le tableau des prédictions.
4. Rechercher une valeur ou filtrer les classes `Churn` et `Not Churn`.
5. Télécharger la sélection en CSV ou Excel.

Le tableau est paginé par groupes de 25 lignes. Les exports contiennent toutes les lignes correspondant à la recherche et au filtre, pas uniquement la page affichée.

Un [exemple CSV fictif](data/example_customers.csv) est inclus et peut aussi être téléchargé depuis l’interface. Les imports sont limités à **10 000 clients** et **5 Mo** par requête.

## Installation

Prérequis : **Python 3.11**.

```bash
git clone https://github.com/mohamed-maiski/ChurnPrediction-Telecom.git
cd ChurnPrediction-Telecom
python -m venv .venv
```

### Windows PowerShell

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

### Linux / macOS

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Ouvrir **[http://127.0.0.1:5000](http://127.0.0.1:5000)**. Arrêter le serveur avec `Ctrl+C`.

## Données

Les fichiers CSV sont directement regroupés dans `data/` :

| Fichier | Utilisation |
| --- | --- |
| [telco_customers.csv](data/telco_customers.csv) | Jeu de données pour l’exploration et l’entraînement dans les notebooks |
| [example_customers.csv](data/example_customers.csv) | Trois profils fictifs pour tester les prédictions individuelles et par fichier |

Le jeu d’étude provient du [projet IBM Telco Customer Churn](https://github.com/IBM/telco-customer-churn-on-icp4d). Les conditions de distribution de cette source sont disponibles dans sa [licence](https://github.com/IBM/telco-customer-churn-on-icp4d/blob/master/LICENSE).

### Format des fichiers clients

| Colonne | Valeurs attendues |
| --- | --- |
| `SeniorCitizen` | `Yes`, `No`, `1` ou `0` |
| `Dependents` | `Yes` ou `No` |
| `tenure` | Nombre entier de mois, positif ou nul |
| `OnlineSecurity` | `Yes`, `No` ou `No internet service` |
| `OnlineBackup` | `Yes`, `No` ou `No internet service` |
| `DeviceProtection` | `Yes`, `No` ou `No internet service` |
| `TechSupport` | `Yes`, `No` ou `No internet service` |
| `Contract` | `Month-to-month`, `One year` ou `Two year` |
| `MonthlyCharges` | Nombre positif ou nul |
| `TotalCharges` | Nombre positif ou nul |

Utiliser des données brutes, avant encodage et normalisation. Les CSV peuvent employer la virgule ou le point-virgule comme séparateur ; les décimales utilisent un point. L’import Excel lit la première feuille.

Les colonnes supplémentaires sont ignorées. Les catégories inconnues, valeurs manquantes et nombres invalides sont signalés dans la page. Les données importées et les résultats sont traités en mémoire, sans enregistrement automatique sur le disque du serveur.

## Organisation du projet

```text
ChurnPrediction-Telecom/
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
├── data/
│   ├── telco_customers.csv
│   └── example_customers.csv
├── models/
│   ├── random_forest_model.pkl
│   └── label_encoders_and_scaler.pkl
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_model_training.ipynb
│   └── 03_prediction_usage.ipynb
├── static/
│   ├── css/style.css
│   ├── js/index.js
│   └── images/
├── templates/
│   └── index.html
└── tests/
    └── test_app.py
```

## Notebooks

| Notebook | Contenu |
| --- | --- |
| [01_data_exploration.ipynb](notebooks/01_data_exploration.ipynb) | Exploration, qualité des données et préparation des variables |
| [02_model_training.ipynb](notebooks/02_model_training.ipynb) | Entraînement et évaluation d’une nouvelle forêt, avec séparation entraînement/test avant l’ajustement des transformations |
| [03_prediction_usage.ipynb](notebooks/03_prediction_usage.ipynb) | Utilisation du modèle intégré sur les profils d’exemple |

Chaque notebook se lance indépendamment. Pour les ouvrir, utiliser l’environnement Python du projet :

```bash
python -m pip install jupyterlab
python -m jupyterlab
```

Les données sont lues directement depuis `data/`. Le notebook d’entraînement conserve ses nouveaux modèles en mémoire et ne remplace pas les artefacts utilisés par l’application.

## Modèle

L’application utilise les deux fichiers enregistrés dans `models/`. Les catégories sont encodées avec les transformations fournies ; seules `tenure`, `MonthlyCharges` et `TotalCharges` sont normalisées.

La version scikit-learn **1.4.1.post1**, utilisée pour enregistrer les artefacts, est conservée dans les dépendances. L’évaluation du notebook concerne la nouvelle forêt entraînée, pas les modèles historiques intégrés à l’application.

Les résultats sont des classes prédites et non des probabilités calibrées. L’application est destinée à une démonstration locale.

## Tests

```bash
python -m unittest discover -s tests -v
```

Les tests couvrent les prédictions individuelles et par fichier, les imports CSV / Excel, les données invalides, les exports Excel et le téléchargement de l’exemple CSV.

## Technologies

Python · Flask · pandas · NumPy · scikit-learn · openpyxl · HTML · CSS · JavaScript
