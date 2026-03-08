# 🌾 AgroSync: Agricultural Disaster Prediction & Management System

A comprehensive AI-powered platform for predicting and managing agricultural disasters including drought, flooding, and heatwaves. Using machine learning models trained on weather and environmental data, AgroSync provides early warnings and tactical decisions to protect crops and aid disaster relief efforts.

## 📋 Features

- **Drought Prediction**: Predicts drought conditions using rainfall deficit and temperature anomalies
- **Flood Risk Detection**: Identifies flood risks based on precipitation patterns and terrain data
- **Heatwave Alerting**: Detects extreme temperature conditions threatening crop yields
- **Live Weather Integration**: Fetches real-time weather data from Open-Meteo API
- **Geographic Analysis**: Interactive maps showing hazard zones and affected areas
- **Multi-Model Inference**: Uses multiple trained ML models for accurate predictions
- **Admin Dashboard**: Manage predictions, view historical data, and configure alerts
- **Relief Coordination**: Tactical engine for disaster relief deployment and resource allocation
- **Bot Integration**: Automated notification system for emergency alerts

## 🏗️ Project Structure

```
Agro_project/
├── src/                          # Main application files
│   ├── app_v2.py               # Flask backend API
│   ├── dashboard.py            # Streamlit dashboard UI
│   ├── bot.py                  # Alert notification bot
│   └── admin.py                # Admin panel
│
├── models/                       # Model training scripts
│   ├── make_brain.py           # General drought/disaster model training
│   ├── make_flood_brain.py     # Flood prediction model training
│   └── make_heatwave_brain.py  # Heatwave prediction model training
│
├── data/                         # Data storage
│   ├── trained_models/         # Serialized ML models (.pkl files)
│   │   ├── disaster_brain.pkl
│   │   ├── drought_brain.pkl
│   │   ├── flood_brain.pkl
│   │   └── heatwave_brain.pkl
│   │
│   ├── datasets/               # Raw and processed datasets
│   │   ├── drought_dataset.csv.xlsx
│   │   └── stage_4_drought_dataset_ALCHEMIST.xlsx
│   │
│   └── state/                  # Runtime state and logs
│       └── alert_state.json
│
├── pages/                        # Streamlit multi-page app
│   ├── 1_Relief_Brain.py       # Disaster relief coordination
│   └── 2_Tactical_Engine.py    # Tactical decision support
│
├── config/                       # Configuration files (future use)
├── utils/                        # Utility functions (future use)
├── docs/                         # Documentation (future use)
│
├── requirements.txt              # Python dependencies
├── .gitignore                   # Git ignore patterns
└── README.md                    # This file

```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip or conda
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Agro_project
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Train the models** (if needed)
   ```bash
   python models/make_brain.py          # General disaster prediction
   python models/make_flood_brain.py    # Flood model
   python models/make_heatwave_brain.py # Heatwave model
   ```

### Running the Application

**Option 1: Streamlit Dashboard (Recommended)**
```bash
streamlit run src/dashboard.py
```
Access the dashboard at `http://localhost:8501`

**Option 2: Flask Backend API**
```bash
python src/app_v2.py
```
API will run on `http://localhost:5000`

**Option 3: Admin Panel**
```bash
python src/admin.py
```

## 📊 How It Works

### Model Pipeline

1. **Data Collection**: Real-time weather data fetched from Open-Meteo API (90+ days of historical data)
2. **Feature Engineering**: Calculating metrics like:
   - 90-day rainfall sum
   - 30-day average temperature
   - Temperature anomalies
   - Precipitation patterns

3. **Model Inference**: Pre-trained models predict probability of:
   - **Drought** (rainfall deficit & high temperature)
   - **Flood** (excess precipitation)
   - **Heatwave** (temperature extremes)

4. **Alert Generation**: Based on probability thresholds:
   - 🟢 Low Impact (≤30%)
   - 🟡 Moderate Impact (30-60%)
   - 🟠 High Impact (60-80%)
   - 🔴 SEVERE IMPACT (>80%)

5. **Relief Coordination**: Tactical engine suggests relief measures and resource allocation

## 📦 Core Dependencies

- **Flask**: Web framework for API
- **Streamlit**: Interactive UI dashboard
- **Pandas & NumPy**: Data processing
- **Joblib**: Model serialization
- **Scikit-learn**: ML models
- **Plotly**: Interactive visualizations
- **Folium**: Geographic mapping

See `requirements.txt` for complete list with versions.

## 🔧 Configuration

- **Latitude/Longitude**: Modify in dashboard to specify agricultural region
- **Thresholds**: Adjust hazard probability thresholds in model scripts
- **API Keys**: Add Open-Meteo API configuration if using authentication
- **Alert Settings**: Configure in `data/state/alert_state.json`

## 📝 Data Formats

### Trained Models (.pkl)
Serialized joblib objects containing:
- `model`: Trained scikit-learn classifier/regressor
- `features`: Expected feature names for predictions
- `metadata`: Model info and training date

### Datasets (.xlsx, .csv)
- Labeled historical weather data
- Agricultural outcome records
- Feature engineering results

### Alert State (JSON)
```json
{
  "last_alert": "2026-03-07",
  "active_alerts": [],
  "threshold_adjustments": {}
}
```

## 🤝 Contributing

To add new features:

1. Create a new branch: `git checkout -b feature/your-feature`
2. Make changes and test thoroughly
3. Commit and push: `git push origin feature/your-feature`
4. Submit a pull request

## 📄 License

[Specify your license here - e.g., MIT, Apache 2.0, etc.]

## 👥 Team

- **Developer**: [Your Name]
- **Domain Expert**: [Agricultural/Meteorology Expert]

## 📞 Support

For issues, questions, or feedback:
- Open an issue on GitHub
- Contact: [Your Contact Info]

## 🗺️ Roadmap

- [ ] Real-time mobile alerts via SMS/WhatsApp
- [ ] Multi-language support
- [ ] Advanced ensemble models
- [ ] Historical trend analysis
- [ ] Crop-specific impact modeling
- [ ] Integration with government agencies
- [ ] Community feedback system

---

**Last Updated**: March 2026  
**Status**: Active Development
