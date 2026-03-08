from flask import Flask, request, jsonify
import joblib
import pandas as pd
import numpy as np

app = Flask(__name__)

# 1. LOAD THE BRAIN
print("🔌 Booting up server...")
try:
    artifact = joblib.load("drought_brain.pkl")
    model = artifact['model']
    feature_names = artifact['features']
    print("🧠 Brain loaded successfully!")
except Exception as e:
    print(f"💀 CRITICAL ERROR: Could not load model. Run train_and_save.py first! {e}")
    model = None

@app.route('/')
def home():
    return "🌍 AgroSync AI is Online. Send POST requests to /predict"

@app.route('/predict', methods=['POST'])
def predict():
    if not model:
        return jsonify({'error': 'Model not loaded'}), 500

    try:
        # 1. Get JSON data from the user/ESP32
        data = request.json
        print(f"📨 Received data: {data}")

        # 2. Turn JSON into a DataFrame
        # We need to manually calculate the rolling features or ask the user for them.
        # For simplicity in V1, let's assume the ESP32 sends the raw daily data 
        # and we approximate the long-term history (or the ESP32 tracks it).
        
        # NOTE: In a real production app, you'd fetch the last 90 days from a database here.
        # For this demo, we'll expect the user to send the averages.
        
        input_data = [data.get(f, 0) for f in feature_names]
        
        # 3. Predict
        probability = model.predict_proba([input_data])[0][1] # Probability of Class 1
        
        # 4. Generate Human Explanation
        status = "DANGER 🚨" if probability > 0.6 else "SAFE ✅"
        
        explanation = f"Drought Risk is {int(probability*100)}%."
        if data.get('rain_90d_sum', 100) < 50:
            explanation += " Severe rainfall deficit detected."
        
        response = {
            'risk_score': probability,
            'status': status,
            'message': explanation
        }
        
        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    # Host='0.0.0.0' allows other devices on WiFi to connect
    app.run(host='0.0.0.0', port=5000, debug=True)
