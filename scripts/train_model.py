import argparse
import hashlib
import json
import pickle
import sys
from pathlib import Path

import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import CATEGORIES, NUMERIC, preprocess_new_data, validate_data


def prepare_training_data(frame):
    if 'Churn' not in frame.columns:
        raise ValueError('The training dataset must include Churn.')
    frame = frame.copy()
    frame['TotalCharges'] = pd.to_numeric(frame['TotalCharges'], errors='coerce')
    frame = frame.dropna(subset=['TotalCharges'])
    target = frame['Churn'].astype('string').str.strip().map({'No': 0, 'Yes': 1, '0': 0, '1': 1})
    if target.isna().any() or target.nunique() != 2:
        raise ValueError('Churn must contain both No and Yes classes.')
    return validate_data(frame, max_rows=None), target.astype(int)


def train_model(frame, random_state=42):
    features, target = prepare_training_data(frame)
    train_x, test_x, train_y, test_y = train_test_split(
        features, target, test_size=0.2, random_state=random_state, stratify=target,
    )
    encoders = {column: LabelEncoder().fit(train_x[column]) for column in CATEGORIES}
    scaler = StandardScaler().fit(train_x[NUMERIC])
    model = RandomForestClassifier(
        n_estimators=200, max_depth=9, class_weight='balanced', random_state=random_state,
    )
    model.fit(preprocess_new_data(train_x, encoders, scaler), train_y)
    transformed_test = preprocess_new_data(test_x, encoders, scaler)
    predictions = model.predict(transformed_test)
    probabilities = model.predict_proba(transformed_test)[:, list(model.classes_).index(1)]
    metrics = {
        'model': 'RandomForestClassifier',
        'sklearn_version': sklearn.__version__,
        'random_state': random_state,
        'rows_received': len(frame),
        'rows_used': len(features),
        'rows_excluded_missing_total_charges': len(frame) - len(features),
        'train_rows': len(train_x),
        'test_rows': len(test_x),
        'accuracy': accuracy_score(test_y, predictions),
        'precision': precision_score(test_y, predictions, zero_division=0),
        'recall': recall_score(test_y, predictions, zero_division=0),
        'f1': f1_score(test_y, predictions, zero_division=0),
        'roc_auc': roc_auc_score(test_y, probabilities),
        'confusion_matrix': confusion_matrix(test_y, predictions, labels=[0, 1]).tolist(),
    }
    return model, encoders, scaler, metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, default=ROOT / 'data/raw/telco_customers.csv')
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/retrained')
    arguments = parser.parse_args()
    source = arguments.data.read_bytes()
    frame = pd.read_csv(arguments.data)
    model, encoders, scaler, metrics = train_model(frame)
    metrics['dataset_sha256'] = hashlib.sha256(source).hexdigest()
    arguments.output.mkdir(parents=True, exist_ok=True)
    with (arguments.output / 'random_forest_model.pkl').open('wb') as file:
        pickle.dump(model, file)
    with (arguments.output / 'label_encoders_and_scaler.pkl').open('wb') as file:
        pickle.dump((encoders, scaler), file)
    (arguments.output / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    main()
