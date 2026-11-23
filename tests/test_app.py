import io
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from app import app, FEATURES, FORM_FIELDS, NUMERIC, ROOT, label_encoders, scaler, preprocess_new_data, validate_data


class PredictionTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.frame = pd.read_csv(ROOT / 'data/example_customers.csv')

    def upload(self, content, filename):
        response = self.client.post('/predict', data={'file_csv': (io.BytesIO(content), filename)}, buffered=True)
        response.request.environ['wsgi.input'].close()
        response.close()
        return response

    def test_home(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('lang="en"', response.get_data(as_text=True))

    def test_single_matches_batch(self):
        batch = self.upload(self.frame.to_csv(index=False).encode(), 'clients.csv')
        self.assertEqual(batch.status_code, 200, batch.json)
        form = {field: str(self.frame.iloc[0][column]) for column, field in zip(FEATURES, FORM_FIELDS)}
        single = self.client.post('/predict', data=form)
        self.assertEqual(single.status_code, 200, single.json)
        self.assertEqual(single.json['churn'], batch.json['rows'][0]['Churn Prediction'] == 'Churn')
        self.assertEqual(len(batch.json['rows']), 3)

    def test_preprocessing_uses_only_numeric_scaler_features(self):
        validated = validate_data(self.frame)
        transformed = preprocess_new_data(validated, label_encoders, scaler)
        self.assertEqual(list(transformed.columns), FEATURES)
        np.testing.assert_allclose(transformed[NUMERIC], scaler.transform(validated[NUMERIC]))
        for column, encoder in label_encoders.items():
            np.testing.assert_array_equal(transformed[column], encoder.transform(validated[column]))

    def test_excel(self):
        output = io.BytesIO()
        self.frame.to_excel(output, index=False)
        response = self.upload(output.getvalue(), 'clients.xlsx')
        self.assertEqual(response.status_code, 200, response.json)
        self.assertEqual(len(response.json['rows']), 3)

    def test_semicolon_and_numeric_senior(self):
        self.frame['SeniorCitizen'] = [0, 1, 0]
        response = self.upload(self.frame.to_csv(index=False, sep=';').encode('utf-8-sig'), 'clients.csv')
        self.assertEqual(response.status_code, 200, response.json)

    def test_invalid_inputs(self):
        cases = [self.frame.drop(columns='Contract'), self.frame.iloc[:0],
                 self.frame.assign(tenure=-1), self.frame.assign(TotalCharges=''),
                 self.frame.assign(MonthlyCharges=float('inf')), self.frame.assign(Contract='<script>')]
        for frame in cases:
            with self.subTest(columns=list(frame.columns), size=len(frame)):
                response = self.upload(frame.to_csv(index=False).encode(), 'clients.csv')
                self.assertEqual(response.status_code, 400)
                self.assertIn('error', response.json)
        self.assertEqual(self.client.post('/predict', data={}).status_code, 400)
        self.assertEqual(self.upload(b'bad', 'clients.xls').status_code, 400)
        self.assertEqual(self.upload(b'bad', 'clients.xlsx').status_code, 400)

    def test_upload_limit(self):
        response = self.upload(b'x' * (5 * 1024 * 1024 + 1), 'large.csv')
        self.assertEqual(response.status_code, 413)
        self.assertIn('error', response.json)

    def test_row_limit(self):
        with self.assertRaisesRegex(ValueError, '10,000'):
            validate_data(pd.concat([self.frame] * 3334, ignore_index=True))

    def test_requests_are_independent(self):
        self.upload(self.frame.to_csv(index=False).encode(), 'clients.csv')
        other = app.test_client()
        self.assertEqual(other.get('/filter?filter_with=Churn').status_code, 404)
        self.assertEqual(self.upload(b'bad', 'bad.txt').status_code, 400)


    def test_duplicate_csv_headers(self):
        content = self.frame.to_csv(index=False).replace('SeniorCitizen,Dependents', 'SeniorCitizen,SeniorCitizen')
        response = self.upload(content.encode(), 'duplicate.csv')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Duplicate', response.json['error'])

    def test_whitespace_and_whole_months(self):
        self.frame['SeniorCitizen'] = [' 0 ', ' 1 ', ' 0 ']
        self.assertEqual(self.upload(self.frame.to_csv(index=False).encode(), 'clients.csv').status_code, 200)
        self.frame['tenure'] = 1.5
        self.assertEqual(self.upload(self.frame.to_csv(index=False).encode(), 'clients.csv').status_code, 400)

    def test_prediction_responses_are_not_cached(self):
        response = self.upload(self.frame.to_csv(index=False).encode(), 'clients.csv')
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')

    def test_unexpected_model_error_is_generic(self):
        with patch('app.predict_customers', side_effect=RuntimeError('private details')):
            with self.assertLogs(app.logger, level='ERROR'):
                response = self.upload(self.frame.to_csv(index=False).encode(), 'clients.csv')
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('private details', response.get_data(as_text=True))


    def test_excel_export_roundtrip(self):
        prediction = self.upload(self.frame.to_csv(index=False).encode(), 'clients.csv').json
        selected = prediction['rows'][:2]
        response = self.client.post('/export/xlsx', json={'rows': selected})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertIn('telecom_predictions.xlsx', response.headers['Content-Disposition'])
        exported = pd.read_excel(io.BytesIO(response.data))
        self.assertEqual(list(exported.columns), FEATURES + ['Churn Prediction'])
        self.assertEqual(len(exported), 2)
        self.assertEqual(exported['Churn Prediction'].tolist(), [row['Churn Prediction'] for row in selected])

    def test_excel_export_rejects_invalid_rows(self):
        for payload in [None, {}, {'rows': []}, {'rows': ['invalid']}, {'rows': [{'Contract': '=1+1'}]}]:
            with self.subTest(payload=payload):
                self.assertEqual(self.client.post('/export/xlsx', json=payload).status_code, 400)

    def test_empty_file(self):
        response = self.upload(b'', 'empty.csv')
        self.assertEqual(response.status_code, 400)
        self.assertIn('empty', response.json['error'])


    def test_example_download(self):
        with self.client.get('/example.csv') as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn('example_customers.csv', response.headers['Content-Disposition'])
            downloaded = pd.read_csv(io.BytesIO(response.data))
            self.assertEqual(list(downloaded.columns), FEATURES)
            self.assertEqual(len(downloaded), len(self.frame))


if __name__ == '__main__':
    unittest.main()
