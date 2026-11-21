import csv
import io
import pickle
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.exceptions import RequestEntityTooLarge

ROOT = Path(__file__).resolve().parent
FEATURES = [
    'SeniorCitizen', 'Dependents', 'tenure', 'OnlineSecurity', 'OnlineBackup',
    'DeviceProtection', 'TechSupport', 'Contract', 'MonthlyCharges', 'TotalCharges',
]
NUMERIC = ['tenure', 'MonthlyCharges', 'TotalCharges']
CATEGORIES = {
    'SeniorCitizen': ['No', 'Yes'],
    'Dependents': ['No', 'Yes'],
    'OnlineSecurity': ['No', 'No internet service', 'Yes'],
    'OnlineBackup': ['No', 'No internet service', 'Yes'],
    'DeviceProtection': ['No', 'No internet service', 'Yes'],
    'TechSupport': ['No', 'No internet service', 'Yes'],
    'Contract': ['Month-to-month', 'One year', 'Two year'],
}
FORM_FIELDS = [
    'SeniorCitizen', 'Dependents', 'tenure', 'onlinesecurity', 'onlinebackup',
    'DeviceProtection', 'techsupport', 'contract', 'monthlycharges', 'totalcharges',
]
MAX_ROWS = 10000
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def preprocess_new_data(frame, encoders, fitted_scaler):
    transformed = frame.copy()
    for column, encoder in encoders.items():
        transformed[column] = encoder.transform(transformed[column])
    transformed[NUMERIC] = fitted_scaler.transform(transformed[NUMERIC])
    return transformed.loc[:, FEATURES]



def validate_data(frame, max_rows=MAX_ROWS):
    if frame.columns.duplicated().any():
        raise ValueError('Duplicate column names are not supported.')
    missing = [column for column in FEATURES if column not in frame.columns]
    if missing:
        raise ValueError('Missing columns: ' + ', '.join(missing))
    if frame.empty:
        raise ValueError('The file does not contain any customers.')
    if max_rows is not None and len(frame) > max_rows:
        raise ValueError(f'Please limit each import to {max_rows:,} customers.')
    frame = frame.loc[:, FEATURES].copy()
    senior = frame['SeniorCitizen'].astype('string').str.strip()
    frame['SeniorCitizen'] = senior.replace({'0': 'No', '1': 'Yes', '0.0': 'No', '1.0': 'Yes'})
    for column, categories in CATEGORIES.items():
        frame[column] = frame[column].astype('string').str.strip()
        if not frame[column].isin(categories).all():
            raise ValueError(f'{column}: accepted values are ' + ', '.join(categories) + '.')
    for column in NUMERIC:
        frame[column] = pd.to_numeric(frame[column], errors='coerce')
        if not np.isfinite(frame[column]).all() or (frame[column] < 0).any():
            raise ValueError(f'{column}: enter non-negative numbers, without missing values.')
    if (frame['tenure'] % 1 != 0).any():
        raise ValueError('tenure: enter a whole number of months.')
    return frame


def read_upload(upload):
    suffix = Path(upload.filename or '').suffix.lower()
    if suffix == '.csv':
        try:
            text = upload.read().decode('utf-8-sig')
        except UnicodeDecodeError as error:
            raise ValueError('Save the CSV file with UTF-8 encoding, then try again.') from error
        if not text.strip():
            raise ValueError('The file is empty.')
        first_line = next(line for line in text.splitlines() if line.strip())
        delimiter = ';' if first_line.count(';') > first_line.count(',') else ','
        headers = [name.strip() for name in next(csv.reader([first_line], delimiter=delimiter))]
        if len(headers) != len(set(headers)):
            raise ValueError('Duplicate column names are not supported.')
        frame = pd.read_csv(io.StringIO(text), sep=delimiter, nrows=MAX_ROWS + 1)
    elif suffix == '.xlsx':
        try:
            content = upload.read()
            with ZipFile(io.BytesIO(content)) as workbook:
                if sum(item.file_size for item in workbook.infolist()) > 50 * 1024 * 1024:
                    raise ValueError('This workbook is too large after decompression.')
            frame = pd.read_excel(io.BytesIO(content), engine='openpyxl', nrows=MAX_ROWS + 1)
        except (BadZipFile, KeyError) as error:
            raise ValueError('The Excel file is invalid or damaged.') from error
    else:
        raise ValueError('Choose a CSV or Excel (.xlsx) file.')
    frame.columns = frame.columns.astype(str).str.strip()
    return frame


with (ROOT / 'models/label_encoders_and_scaler.pkl').open('rb') as file:
    label_encoders, scaler = pickle.load(file)
with (ROOT / 'models/random_forest_model.pkl').open('rb') as file:
    model = pickle.load(file)


def predict_customers(frame):
    return model.predict(preprocess_new_data(frame, label_encoders, scaler))


app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_BYTES


@app.get('/')
def home():
    return render_template('index.html', categories=CATEGORIES)


@app.post('/predict')
def predict():
    batch = 'file_csv' in request.files
    try:
        if batch:
            frame = read_upload(request.files['file_csv'])
        else:
            if any(field not in request.form for field in FORM_FIELDS):
                raise ValueError('Please complete all fields in the form.')
            frame = pd.DataFrame([{
                column: request.form[field]
                for column, field in zip(FEATURES, FORM_FIELDS)
            }])
        frame = validate_data(frame)
        predictions = predict_customers(frame)
        if batch:
            frame['Churn Prediction'] = ['Churn' if value == 1 else 'Not Churn' for value in predictions]
            return jsonify(mode='table', rows=frame.to_dict(orient='records'), columns=frame.columns.tolist())
        return jsonify(mode='Customer', churn=bool(predictions[0] == 1))
    except (ValueError, pd.errors.ParserError, EOFError) as error:
        return jsonify(error=str(error)), 400
    except Exception:
        app.logger.exception('Prediction failed')
        return jsonify(error='Prediction could not be completed. Please try again.'), 500


@app.post('/export/xlsx')
def export_excel():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get('rows'), list):
        return jsonify(error='Provide a list of prediction rows.'), 400
    rows = data['rows']
    if not rows or not all(isinstance(row, dict) for row in rows):
        return jsonify(error='There are no valid prediction rows to export.'), 400
    try:
        frame = pd.DataFrame(rows)
        validated = validate_data(frame)
        if 'Churn Prediction' not in frame or not frame['Churn Prediction'].isin(['Churn', 'Not Churn']).all():
            raise ValueError('Each row must include a valid Churn Prediction.')
        validated['Churn Prediction'] = frame['Churn Prediction']
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            validated.to_excel(writer, sheet_name='Predictions', index=False)
            worksheet = writer.sheets['Predictions']
            worksheet.freeze_panes = 'A2'
            worksheet.auto_filter.ref = worksheet.dimensions
            for cells in worksheet.columns:
                worksheet.column_dimensions[cells[0].column_letter].width = 22
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name='telecom_predictions.xlsx')
    except ValueError as error:
        return jsonify(error=str(error)), 400


@app.after_request
def response_headers(response):
    if request.path == '/predict' or request.path.startswith('/export/'):
        response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.errorhandler(RequestEntityTooLarge)
def file_too_large(error):
    return jsonify(error='The file exceeds the 5 MB limit.'), 413


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
