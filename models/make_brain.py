import pandas as pd
import numpy as np
import os
import joblib
from sklearn.ensemble import RandomForestClassifier

# ==========================================
# 1. LOAD DATA
# ==========================================
def load_data(folder_path=r"C:\AgroSync_Demo"):
    filename = "drought_dataset.csv.xlsx"
    path = os.path.join(folder_path, filename)
    print(f"📂 Loading data from: {path}")
    return pd.read_excel(path, header=1)

# ==========================================
# 2. CREATE FEATURES & TRAIN
# ==========================================
def create_brain():
    df = load_data()
    
    # Engineer Features (The "History" logic)
    print("🛠️  Teaching the model about history...")
    df['rain_90d_sum'] = df['PRECTOTCORR'].rolling(window=90, min_periods=1).sum()
    df['temp_30d_avg'] = df['T2M'].rolling(window=30, min_periods=1).mean()
    df['humid_30d_avg'] = df['RH2M'].rolling(window=30, min_periods=1).mean()
    df = df.bfill()

    # Define the exact features we want
    features = [
        'rain_90d_sum', 'temp_30d_avg', 'humid_30d_avg', 
        'PRECTOTCORR', 'RH2M', 'T2M_MAX', 'WS2M', 
        'month_sin', 'month_cos'
    ]
    
    X = df[features]
    y = df['label']

    print("🧠 Training the Random Forest...")
    model = RandomForestClassifier(n_estimators=100, max_depth=20, random_state=42)
    model.fit(X, y)

    # ==========================================
    # 3. SAVE THE FILE (CRITICAL STEP!)
    # ==========================================
    print("💾 Saving 'drought_brain.pkl'...")
    
    artifact = {
        'model': model,
        'features': features
    }
    
    # This creates the file your Flask app is looking for
    joblib.dump(artifact, "drought_brain.pkl") 
    print("✅ DONE! Brain saved. Now you can run the server.")

if __name__ == "__main__":
    create_brain()
