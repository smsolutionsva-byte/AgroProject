from flask import Flask, request, jsonify
import joblib
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

# 1. LOAD THE BRAIN
print("🔌 Booting up AI System...")
try:
    artifact = joblib.load("drought_brain.pkl")
    model = artifact['model']
    feature_names = artifact['features']
    print("🧠 Brain loaded! Ready to predict.")
except Exception as e:
    print(f"💀 ERROR: Run 'make_brain.py' first! {e}")
    model = None

# ==========================================
# 2. THE LIVE WEATHER FETCHER (Open-Meteo)
# ==========================================
def get_live_weather_data(lat, lon):
    print(f"🌍 Fetching live data for Lat: {lat}, Lon: {lon}...")
    
    # We need 90 days of history to calculate 'rain_90d_sum'
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=92) # Get a few extra days for safety
    
    # Open-Meteo API URL (Free, No Key needed)
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&daily=temperature_2m_mean,temperature_2m_max,rain_sum,wind_speed_10m_max,relative_humidity_2m_mean&timezone=auto"
    
    try:
        r = requests.get(url)
        data = r.json()
        
        # Convert JSON to Pandas DataFrame
        df = pd.DataFrame({
            'date': data['daily']['time'],
            'PRECTOTCORR': data['daily']['rain_sum'],           # Map to our model names
            'T2M': data['daily']['temperature_2m_mean'],
            'T2M_MAX': data['daily']['temperature_2m_max'],
            'RH2M': data['daily']['relative_humidity_2m_mean'], # Humidity
            'WS2M': data['daily']['wind_speed_10m_max']
        })
        
        # Handle missing data (Open-Meteo sometimes has gaps)
        df = df.fillna(method='ffill').fillna(0)
        
        return df
        
    except Exception as e:
        print(f"❌ API Error: {e}")
        return None

# ==========================================
# 3. THE CALCULATOR (Fixed for JSON)
# ==========================================
def process_live_data(df):
    # Calculate Rolling Averages
    df['rain_90d_sum'] = df['PRECTOTCORR'].rolling(window=90, min_periods=1).sum()
    df['temp_30d_avg'] = df['T2M'].rolling(window=30, min_periods=1).mean()
    df['humid_30d_avg'] = df['RH2M'].rolling(window=30, min_periods=1).mean()
    
    # Get the last date's month
    last_date = pd.to_datetime(df['date'].iloc[-1])
    month = last_date.month
    
    # Force convert EVERYTHING to Python float using float(...)
    # This fixes the "int64 is not JSON serializable" error
    current_features = {
        'rain_90d_sum': float(df['rain_90d_sum'].iloc[-1]),
        'temp_30d_avg': float(df['temp_30d_avg'].iloc[-1]),
        'humid_30d_avg': float(df['humid_30d_avg'].iloc[-1]),
        'PRECTOTCORR': float(df['PRECTOTCORR'].iloc[-1]),
        'RH2M': float(df['RH2M'].iloc[-1]),
        'T2M_MAX': float(df['T2M_MAX'].iloc[-1]),
        'WS2M': float(df['WS2M'].iloc[-1]),
        'month_sin': float(np.sin(2 * np.pi * month / 12)),
        'month_cos': float(np.cos(2 * np.pi * month / 12))
    }
    
    return current_features

# ==========================================
# 4. THE WEB SERVER ROUTES
# ==========================================
@app.route('/live-predict', methods=['GET'])
def live_predict():
    # USAGE: http://localhost:5000/live-predict?lat=19.0&lon=76.0
    
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({"error": "Please provide 'lat' and 'lon' parameters!"})

    # 1. Fetch Data
    df = get_live_weather_data(lat, lon)
    if df is None:
        return jsonify({"error": "Could not fetch weather data from API."})

    # 2. Process Data (Math)
    input_data = process_live_data(df)
    
    # 3. Predict
    # Order the features exactly how the brain expects them
    feature_values = [input_data[f] for f in feature_names]
    
    prob = model.predict_proba([feature_values])[0][1] # Risk Score
    risk_percent = int(prob * 100)
    
    # 4. Create "Farmer Friendly" Response
    status = "DANGER 🚨" if prob > 0.6 else "SAFE ✅"
    
    reasons = []
    if input_data['rain_90d_sum'] < 100:
        reasons.append(f"🌧️ Critical Rain Deficit: Only {int(input_data['rain_90d_sum'])}mm in last 3 months.")
    if input_data['humid_30d_avg'] < 30:
        reasons.append(f"🌵 Soil Air is too dry ({int(input_data['humid_30d_avg'])}% humidity).")
    if prob > 0.6 and not reasons:
        reasons.append("⚠️ Historical weather patterns match past drought years.")

    response = {
        "location": {"lat": lat, "lon": lon},
        "drought_risk": f"{risk_percent}%",
        "status": status,
        "advice": "Irrigation recommended immediately." if prob > 0.6 else "Standard monitoring.",
        "reasons": reasons,
        "debug_data": input_data # Remove this in production if you want cleaner output
    }
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
