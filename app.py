import pandas as pd
from flask import Flask, render_template, request, jsonify
import pickle
import webbrowser

app = Flask(__name__)

def preprocess_new_data(df, label_encoders, scaler):
    for col, le in label_encoders.items():
        df[col] = le.transform(df[col])
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns 
    df[numeric_cols] = scaler.transform(df[numeric_cols])
    return df

with open('models/label_encoders_and_scaler.pkl', 'rb') as f:
    label_encoders, scaler = pickle.load(f)
model = pickle.load(open('models/random_forest_model.pkl', 'rb'))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/test')
def test():
    return render_template('test-projet-table.html')

@app.route('/predict', methods=['POST'])
def predict():
    global model, mode ,df

    if 'file_csv' in request.files:
        try:
            file_csv = pd.read_csv(request.files['file_csv'])
            colonnes_a_garder = ['SeniorCitizen', 'Dependents', 'tenure', 'OnlineSecurity', 'OnlineBackup', 'DeviceProtection', 'TechSupport', 'Contract', 'MonthlyCharges', 'TotalCharges']
            file_csv = file_csv[colonnes_a_garder]
            df = file_csv.copy()
            cust_transformed = preprocess_new_data(file_csv, label_encoders, scaler)
            predictions = model.predict(cust_transformed)
            mode = 'table'
            df['Churn Prediction'] = ['Not Churn' if pred == 0 else 'Churn' for pred in predictions]
            df.to_csv('predicted_data.csv', index=False)
            table_html = df.to_html(classes='table table-bordered table-hover display', index=False)
        except Exception as e:
            table_html = f"<h1><em style='color:red'>Error:</em> {str(e)}</h1>"
        return jsonify({'prediction': table_html, 'mode': mode})
    else:
        try:
            contract = request.form['contract']
            onlinesecurity = request.form['onlinesecurity']
            techsupport = request.form['techsupport']
            onlinebackup = request.form['onlinebackup']
            tenure = float(request.form['tenure'])
            monthlycharges = float(request.form['monthlycharges'])
            totalcharges = float(request.form['totalcharges'])
            seniorcitizen = request.form['SeniorCitizen']
            dependents = request.form['Dependents']
            deviceprotection = request.form['DeviceProtection']
            cust = {
                'SeniorCitizen': [seniorcitizen],
                'Dependents': [dependents],
                'tenure': [tenure],
                'OnlineSecurity': [onlinesecurity],
                'OnlineBackup': [onlinebackup],
                'DeviceProtection': [deviceprotection],
                'TechSupport': [techsupport],
                'Contract': [contract],
                'MonthlyCharges': [monthlycharges],
                'TotalCharges': [totalcharges]
            }
            input_data = pd.DataFrame(cust)
            cust_transformed = preprocess_new_data(input_data, label_encoders, scaler)
            prediction = model.predict(cust_transformed)
            mode = 'Customer'
            prediction_text = '<span class="result-prediction green">Le client est susceptible de continuer !!</span>' if prediction[0] == 0 else '<span class="result-prediction red">Ce client est susceptible de se désabonner !!</span>'
        except Exception as e:
            prediction_text = f"<h1><em style='color:red'>Error:</em> {str(e)}</h1>"
        return jsonify({'prediction': prediction_text, 'mode': mode})
@app.route('/filter', methods=['GET'])
def filter():
    filter_with = request.args.get('filter_with')  # Get filter value from query parameter
    filtered_df = df[df['Churn Prediction'] == filter_with]  # Filter DataFrame based on 'Churn Prediction' column
    mode = 'table'
    table_html = filtered_df.to_html(classes='table table-bordered table-hover', index=False)  # Convert filtered DataFrame to HTML table
    return jsonify({'prediction': table_html, 'mode': mode})  # Return HTML table and mode as JSON response

if __name__ == '__main__':
    webbrowser.open('http://127.0.0.1:5000')
    app.run(host='127.0.0.1', port=5000, debug=False)
