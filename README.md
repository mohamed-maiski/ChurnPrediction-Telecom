# Telecom Customer Churn Prediction

Application web pour estimer le risque de désabonnement des clients télécoms, individuellement ou par fichier CSV / Excel.

![Interface](static/images/interface.jpg)

## Fonctionnalités

- Prédiction individuelle à partir de dix caractéristiques client.
- Import CSV UTF-8 ou Excel `.xlsx`, limité à 10 000 clients et 5 Mo.
- Résultats avec synthèse, recherche, filtres et pagination.
- Export CSV et Excel de toute la sélection.
- Validation des données et interface adaptée aux mobiles.

## Installation

Prérequis : Python 3.11.

```bash
python -m venv .venv
```

Windows PowerShell :

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Linux / macOS :

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Ouvrir [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Utilisation

Choisir **Predict Single Customer** pour analyser un profil ou **Predict from CSV/Excel** pour importer plusieurs clients. Un [exemple fictif](static/examples/customers.csv) est disponible dans la page.

| Colonne | Valeurs attendues |
| --- | --- |
| `SeniorCitizen` | `Yes`, `No`, `1` ou `0` |
| `Dependents` | `Yes` ou `No` |
| `tenure` | Nombre entier de mois, positif ou nul |
| `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport` | `Yes`, `No` ou `No internet service` |
| `Contract` | `Month-to-month`, `One year` ou `Two year` |
| `MonthlyCharges`, `TotalCharges` | Nombres positifs ou nuls |

Utiliser des données brutes, avant encodage et normalisation. Les CSV acceptent la virgule ou le point-virgule comme séparateur ; les décimales utilisent un point. L’import Excel lit la première feuille.

Les résultats sont traités en mémoire, sans enregistrement automatique des données clients sur le serveur. Les exports reprennent toute la sélection, indépendamment de la page affichée.

## Organisation

| Élément | Rôle |
| --- | --- |
| `app.py` | Serveur, validation, prétraitement, prédictions et export Excel |
| `templates/` | Page de l’application |
| `static/` | Styles, JavaScript, images et exemple CSV |
| `models/` | Classifieur Random Forest et transformations enregistrées |
| `notebooks/` | Exploration, entraînement et utilisation du modèle |
| `scripts/` | Téléchargement des données et entraînement |
| `data/README.md` | Source et utilisation des données de recherche |
| `tests/test_app.py` | Tests applicatifs |

## Modèle et notebooks

L’application charge les artefacts fournis dans `models/`. Leur version scikit-learn, `1.4.1.post1`, est conservée dans les dépendances.

Les trois notebooks sont conservés, y compris `03_prediction_usage.ipynb`. Pour les ouvrir, installer JupyterLab dans l’environnement, puis le lancer :

```bash
python -m pip install jupyterlab
python -m jupyterlab
```

Pour télécharger les données et lancer un nouvel entraînement :

```bash
python scripts/download_data.py
python scripts/train_model.py
```

Les nouveaux modèles et métriques sont écrits dans `artifacts/retrained/`, sans remplacer les modèles intégrés. La séparation entraînement/test précède l’ajustement des transformations. Cette évaluation concerne le nouveau modèle, pas les artefacts historiques fournis.

Voir [les instructions sur les données](data/README.md).

## Tests

```bash
python -m unittest discover -s tests -v
```

## Technologies

Python, Flask, pandas, NumPy, scikit-learn, openpyxl, HTML, CSS et JavaScript.

## Périmètre

Les sorties sont des classes prédites, pas des probabilités calibrées. L’application est destinée à une démonstration locale. Les artefacts pickle doivent provenir d’une source de confiance.
