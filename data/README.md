# Données

## Exemple inclus

`static/examples/customers.csv` contient trois profils fictifs pour tester l’interface. Il ne sert pas à mesurer les performances du modèle.

## Données des expériences

Les données de recherche sont conservées localement dans `data/raw/` et `data/processed/`. Les fichiers CSV de ces dossiers sont exclus de Git et du paquet public.

Pour obtenir un jeu de données de référence, consulter le [projet IBM Telco Customer Churn](https://github.com/IBM/telco-customer-churn-on-icp4d) et sa [licence](https://github.com/IBM/telco-customer-churn-on-icp4d/blob/master/LICENSE).

Depuis la racine :

```powershell
.\.venv\Scripts\python.exe scripts/download_data.py
```

Le fichier est enregistré dans `data/raw/telco_customers.csv`. Le script conserve un fichier déjà présent et demande un autre chemin au lieu de l’écraser.

Il est également possible de placer manuellement un CSV dans ce dossier. Il doit contenir les dix variables décrites dans le README principal et une colonne `Churn` avec les classes `Yes` et `No`.

## Préparation

Les valeurs non numériques de TotalCharges sont traitées comme manquantes et les lignes concernées sont exclues de l’entraînement. Le nombre de lignes exclues est enregistré avec les métriques. Les autres valeurs sont validées ; aucune transformation n’est ajustée avant la séparation entraînement/test.
