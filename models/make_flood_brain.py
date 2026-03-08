import pandas as pd
import numpy as np
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# 1. LOAD DATA
def load_data(folder_path=r"C:\AgroSync_Demo"):
    filename = "drought_dataset.csv.xlsx"
    path = os.path.join(folder_path, filename)
    print(f"📂 Loading weather data from: {path}")
    return pd.read_excel(path, header=1)

def create_flood_brain():
    df = load_data()
    
    # 2. CREATE TARGET LABEL (The "Flood" Definition) 🏷️
    # We define a "Flood Risk Day" as one where rain is in the Top 1% of history
    # OR strictly above 50mm (Heavy Rain Warning)
    
    flood_threshold = df['PRECTOTCORR'].quantile(0.99) # Top 1% heaviest rain
    print(f"🌊 Flood Threshold determined as: {flood_threshold:.1f} mm/day")
    
    # Label: 1 if Rain > Threshold, else 0
    df['is_flood'] = np.where(df['PRECTOTCORR'] > flood_threshold, 1, 0)

    # 3. ENGINEER FEATURES (The "Saturation" Logic) 🛠️
    print("🛠️  Engineering Flood Features...")
    
    # Feature 1: The Storm (Today's intensity)
    # Feature 2: The Buildup (Last 3 days rain sum) -> If high, ground is soaked
    df['rain_3d_sum'] = df['PRECTOTCORR'].rolling(window=3).sum()
    
    # Feature 3: The Context (Last 7 days rain sum)
    df['rain_7d_sum'] = df['PRECTOTCORR'].rolling(window=7).sum()
    
    # Feature 4: Soil Moisture Context (If soil is wet, flood is more likely)
    df['humid_3d_avg'] = df['RH2M'].rolling(window=3).mean() 
    
    df = df.bfill() # Fill gaps

    features = [
        'rain_3d_sum', 'rain_7d_sum', 'humid_3d_avg', 
        'PRECTOTCORR', 'RH2M', 'WS2M', # Wind usually accompanies storms
        'month_sin', 'month_cos'
    ]
    
    X = df[features]
    y = df['is_flood']

    # 4. TRAIN (Heavier penalty for missing floods because they are rare)
    print("🧠 Training Flood Prediction Model...")
    # class_weight='balanced' tells the model "Pay EXTRA attention to the rare flood cases!"
    model = RandomForestClassifier(n_estimators=100, max_depth=15, class_weight='balanced', random_state=42)
    model.fit(X, y)

    # 5. SAVE
    print("💾 Saving 'flood_brain.pkl'...")
    artifact = {
        'model': model,
        'features': features,
        'threshold': flood_threshold
    }
    joblib.dump(artifact, "flood_brain.pkl")
    print("✅ DONE! Flood Brain ready.")

if __name__ == "__main__":
    create_flood_brain()
