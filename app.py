import os
import pandas as pd
import numpy as np
from flask import Flask, render_template, request, session, redirect, url_for, flash
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random strong key

# No hardcoded users - dummy validation only

# Global variables for model and data
df_clean = None
model = None
label_encoder = None
feature_names = None

# ------------------------------------------------------------
# Data preprocessing
# ------------------------------------------------------------
def load_and_preprocess_data(file_path):
    df = pd.read_csv(file_path)

    # Extract magnitude from 'title'
    if 'title' in df.columns:
        df['magnitude'] = df['title'].str.extract(r'M\s*([\d\.]+)').astype(float)
    else:
        raise KeyError("Column 'title' not found.")

    # Extract CDI from 'magnitude_date_time_cdi'
    if 'magnitude_date_time_cdi' in df.columns:
        df['cdi'] = df['magnitude_date_time_cdi'].str.split().str[0].astype(float)
    else:
        raise KeyError("Column 'magnitude_date_time_cdi' not found.")

    required_cols = ['mmi', 'depth', 'tsunami']
    for col in required_cols:
        if col not in df.columns:
            raise KeyError(f"Required column '{col}' missing.")

    # Extract alert colour
    if 'alert' in df.columns:
        df['alert_colour'] = df['alert'].str.split().str[-1].str.lower()
    else:
        raise KeyError("Column 'alert' not found.")

    features = ['magnitude', 'depth', 'cdi', 'mmi', 'tsunami']
    target = 'alert_colour'

    df_clean = df[features + [target]].dropna()
    le = LabelEncoder()
    df_clean['alert_encoded'] = le.fit_transform(df_clean[target])

    print("Label mapping:", dict(zip(le.classes_, le.transform(le.classes_))))
    return df_clean, le, features

def train_model(df, features):
    X = df[features].values
    y = df['alert_encoded'].values
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

# ------------------------------------------------------------
# Load data and train model
# ------------------------------------------------------------
DATASET_PATH = 'earthquake.csv'
try:
    df_clean, label_encoder, feature_names = load_and_preprocess_data(DATASET_PATH)
    model = train_model(df_clean, feature_names)
    print("✅ Model trained successfully. Samples:", len(df_clean))
except Exception as e:
    print(f"❌ Error loading dataset: {e}")
    model = None

# ------------------------------------------------------------
# Login protection before each request
# ------------------------------------------------------------
# Login protection removed - dummy login screen only

# ------------------------------------------------------------
# Routes
# ------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if '@' in email and len(password) > 0:
            session['user'] = email
            flash('Login successful!', 'success')
            return redirect(url_for('predict'))
        else:
            flash('Email must contain @ and password required', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def predict():
    prediction = None
    alert_colour = None
    error = None

    if request.method == 'POST':
        if model is None:
            error = "Model not loaded. Please check dataset."
        else:
            try:
                magnitude = float(request.form['magnitude'])
                depth = float(request.form['depth'])
                cdi = float(request.form['cdi'])
                mmi = float(request.form['mmi'])
                tsunami = int(request.form['tsunami'])

                # Validation
                if magnitude < 0 or magnitude > 10:
                    error = "Magnitude must be between 0 and 10."
                elif depth < 0:
                    error = "Depth must be positive."
                elif cdi < 0 or cdi > 10:
                    error = "CDI must be between 0 and 10."
                elif mmi < 0 or mmi > 10:
                    error = "MMI must be between 0 and 10."
                elif tsunami not in [0, 1]:
                    error = "Tsunami must be 0 or 1."
                else:
                    input_data = np.array([[magnitude, depth, cdi, mmi, tsunami]])
                    pred_encoded = model.predict(input_data)[0]
                    alert_colour = label_encoder.inverse_transform([pred_encoded])[0].capitalize()
                    prediction = alert_colour

                    risk_map = {
                        'Green': 'Low Risk',
                        'Yellow': 'Moderate Risk',
                        'Orange': 'High Risk',
                        'Red': 'Severe Risk'
                    }
                    prediction = risk_map.get(alert_colour, 'Unknown')
            except ValueError:
                error = "Invalid input. Please enter numeric values."
            except Exception as e:
                error = f"Prediction error: {e}"

    return render_template('predict.html',
                           prediction=prediction,
                           alert_colour=alert_colour,
                           error=error)

@app.route('/samples')
def samples():
    if df_clean is None:
        return "No data loaded", 500
    sample_data = df_clean.head(20).to_dict('records')
    return render_template('samples.html', samples=sample_data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
