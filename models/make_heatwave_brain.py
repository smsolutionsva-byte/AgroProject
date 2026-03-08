import pandas as pd
import numpy as np
import os
import joblib
from sklearn.ensemble import RandomForestClassifier

# 1. LOAD DATA
def load_data(folder_path=r"C:\AgroSync_Demo"):
    # Using your existing file!
    filename = "drought_dataset.csv.xlsx"
    path = os.path.join(folder_path, filename)
    print(f"📂 Loading weather data from: {path}")
    return pd.read_excel(path, header=1)

def create_heatwave_brain():
    df = load_data()
    
    # 2. CREATE TARGET LABEL (Auto-Labeling) 🏷️
    # We define a "Heatwave" as days where Max Temp is in the top 5% of history
    # OR strictly above 40°C (You can adjust this threshold)
    
    heat_threshold = df['T2M_MAX'].quantile(0.95) # Top 5% hottest days
    print(f"🔥 Heatwave Threshold determined as: {heat_threshold:.1f}°C")
    
    # Label: 1 if Max Temp > Threshold, else 0
    df['is_heatwave'] = np.where(df['T2M_MAX'] > heat_threshold, 1, 0)

    # 3. ENGINEER FEATURES (Short-Term Focus) ⚡
    print("🛠️  Engineering features...")
    
    # Heatwaves care about the last 3-7 days, not 90 days.
    df['temp_3d_avg'] = df['T2M'].rolling(window=3).mean()
    df['temp_7d_max'] = df['T2M_MAX'].rolling(window=7).max()
    df['humid_3d_avg'] = df['RH2M'].rolling(window=3).mean() # Humidity makes heat worse!
    
    df = df.bfill() # Fill gaps

    features = [
        'temp_3d_avg', 'temp_7d_max', 'humid_3d_avg', 
        'T2M_MAX', 'T2M', 'RH2M', 'WS2M', 
        'month_sin', 'month_cos'
    ]
    
    X = df[features]
    y = df['is_heatwave']

    # 4. TRAIN
    print("🧠 Training Heatwave Random Forest...")
    model = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42)
    model.fit(X, y)

    # 5. SAVE
    print("💾 Saving 'heatwave_brain.pkl'...")
    artifact = {
        'model': model,
        'features': features,
        'threshold': heat_threshold # Save this to show the user later
    }
    joblib.dump(artifact, "heatwave_brain.pkl")
    print("✅ DONE! Heatwave Brain ready.")

if __name__ == "__main__":
    create_heatwave_brain()
