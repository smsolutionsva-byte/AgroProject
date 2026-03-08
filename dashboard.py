import streamlit as st
import pandas as pd
import numpy as np
import requests
import joblib
import folium
import warnings
import os
from streamlit_folium import st_folium
from datetime import datetime
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
from utils.ui import inject_global_css, render_sidebar, page_header
from utils.gemini import ai_hazard_briefing

warnings.filterwarnings("ignore", category=UserWarning)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# ── Page Config ──────────────────────────────────────────────────────────────
# Added initial_sidebar_state so it always starts open!
st.set_page_config(page_title="AgroSync AI", page_icon="🌾", layout="wide", initial_sidebar_state="expanded")
inject_global_css()

# THE MAGIC FIX: Resurrect the sidebar toggle button from the shadow realm 🧙‍♂️✨
st.markdown("""
    <style>
        /* Force the sidebar toggle button to stay visible no matter what */
        [data-testid="collapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            z-index: 999999 !important;
        }
        /* If the header was completely nuked by your UI utils, we bring it back but make it invisible so the button still works */
        header[data-testid="stHeader"] {
            visibility: visible !important;
            background-color: transparent !important;
        }
    </style>
""", unsafe_allow_html=True)


# ── Helper Functions ─────────────────────────────────────────────────────────
def get_impact_level(prob):
    if prob <= 30:
        return "Low", "low"
    elif prob <= 60:
        return "Moderate", "medium"
    else:
        return "High", "high"


def generate_explanation(hazard_type, features, prob):
    reasons = []
    if hazard_type == "drought":
        if features["rain_90d_sum"] < 50:
            reasons.append(f"Severe rainfall deficit — only {features['rain_90d_sum']:.1f} mm in 90 days.")
        elif features["rain_90d_sum"] < 150:
            reasons.append(f"Below-average rainfall — 90-day total is {features['rain_90d_sum']:.1f} mm.")
        if features["temp_30d_avg"] > 30:
            reasons.append(f"High evaporation risk — monthly avg temp {features['temp_30d_avg']:.1f} °C.")
    elif hazard_type == "heatwave":
        if features["T2M_MAX"] > 40:
            reasons.append(f"Critical daily max temp reached {features['T2M_MAX']:.1f} °C.")
        if features["temp_3d_avg"] > features["temp_30d_avg"] + 2:
            reasons.append("Rapid warming — 3-day avg significantly above monthly baseline.")
        if features["humid_3d_avg"] > 70 and features["T2M_MAX"] > 35:
            reasons.append("Dangerous wet-bulb conditions — high humidity with extreme heat.")
    elif hazard_type == "flood":
        if features["rain_3d_sum"] > 50:
            reasons.append(f"Intense short-term rain — {features['rain_3d_sum']:.1f} mm in 3 days.")
        if features["rain_7d_sum"] > 100:
            reasons.append("Soil likely saturated — weekly rainfall exceeds 100 mm.")
        if features["WS2M"] > 20:
            reasons.append(f"High winds at {features['WS2M']:.0f} km/h accompanying storm system.")
    if not reasons and prob > 20:
        reasons.append("Moderate anomaly detected relative to seasonal norms.")
    return reasons


# ── Load ML Models ───────────────────────────────────────────────────────────
@st.cache_resource
def load_brains():
    models = {}
    try:
        d_art = joblib.load("data/trained_models/drought_brain.pkl")
        models["drought"] = (d_art["model"], d_art["features"])
        h_art = joblib.load("data/trained_models/heatwave_brain.pkl")
        models["heatwave"] = (h_art["model"], h_art["features"], h_art["threshold"])
        f_art = joblib.load("data/trained_models/flood_brain.pkl")
        models["flood"] = (f_art["model"], f_art["features"], f_art["threshold"])
        return models
    except Exception as e:
        st.warning(f"⚠️ Model loading issue: {str(e)}")
        return None


# ── Session state defaults ───────────────────────────────────────────────────
if "lat" not in st.session_state:
    st.session_state["lat"] = 12.9716
if "lon" not in st.session_state:
    st.session_state["lon"] = 77.5946
if "location_name" not in st.session_state:
    st.session_state["location_name"] = "Bengaluru"


# ── Sidebar — Navigation & Quick Tools ───────────────────────────────────────
render_sidebar("Dashboard")

# Load models after sidebar is rendered
brains = load_brains()
if not brains:
    st.error("⚠️ Model files not found. Ensure `.pkl` files exist in `data/trained_models/`. Navigation still available in the sidebar.")
    st.stop()


# ── Hero Header ──────────────────────────────────────────────────────────────
page_header("Farm Intelligence Dashboard", "Real-time hazard analysis powered by satellite data & ML models")


# ── Layout: Map + Analysis Panel ─────────────────────────────────────────────
col_map, col_analysis = st.columns([3, 2], gap="large")

with col_map:
    st.markdown("""
    <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.5px; color: #64748b; margin-bottom: 0.5rem;">
        Select Location</div>
    """, unsafe_allow_html=True)
    search_query = st.text_input(
        "Search city or coordinates",
        placeholder="e.g. Bengaluru or 12.97, 77.59",
        label_visibility="collapsed",
    )

    if search_query:
        try:
            if "," in search_query and any(c.isdigit() for c in search_query):
                parts = search_query.split(",")
                st.session_state["lat"] = float(parts[0].strip())
                st.session_state["lon"] = float(parts[1].strip())
                st.session_state["location_name"] = "Custom Coordinates"
            else:
                geolocator = Nominatim(user_agent="agrosync_ai_dashboard", timeout=10)
                loc = geolocator.geocode(search_query)
                if loc:
                    st.session_state["lat"] = loc.latitude
                    st.session_state["lon"] = loc.longitude
                    st.session_state["location_name"] = loc.address.split(",")[0].strip()
                    st.success(f"Found: {loc.address}")
                else:
                    st.warning("Location not found. Try a different search term.")
        except Exception as e:
            st.error(f"Search failed: {e}")

    m = folium.Map(
        location=[st.session_state["lat"], st.session_state["lon"]],
        zoom_start=10,
        tiles="CartoDB positron",
    )
    folium.CircleMarker(
        [st.session_state["lat"], st.session_state["lon"]],
        radius=10, color="#ef4444", fill=True, fill_opacity=0.7,
    ).add_to(m)
    map_data = st_folium(m, height=420, use_container_width=True)

    if map_data and map_data.get("last_clicked"):
        clicked = map_data["last_clicked"]
        if abs(clicked["lat"] - st.session_state["lat"]) > 0.0001:
            st.session_state["lat"] = clicked["lat"]
            st.session_state["lon"] = clicked["lng"]
            st.session_state["location_name"] = "Map Selection"
            st.rerun()


# ── Fetch & Predict ──────────────────────────────────────────────────────────
lat, lon = st.session_state["lat"], st.session_state["lon"]

with col_analysis:
    st.markdown("""
    <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.5px; color: #64748b; margin-bottom: 0.5rem;">
        Hazard Intelligence</div>
    """, unsafe_allow_html=True)
    st.caption(f"Target: {lat:.4f}, {lon:.4f}")

    if st.button("Analyze Risks", type="primary", use_container_width=True):
        with st.spinner("Fetching live satellite data…"):
            try:
                url = (
                    f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                    "&daily=temperature_2m_mean,temperature_2m_max,precipitation_sum,"
                    "wind_speed_10m_max,relative_humidity_2m_mean"
                    "&past_days=92&forecast_days=1&timezone=auto"
                )
                r = requests.get(url, timeout=15).json()

                if "daily" not in r:
                    st.error("No data available for this location.")
                    st.stop()

                df = pd.DataFrame({
                    "date": pd.to_datetime(r["daily"]["time"]),
                    "PRECTOTCORR": r["daily"]["precipitation_sum"],
                    "T2M": r["daily"]["temperature_2m_mean"],
                    "T2M_MAX": r["daily"]["temperature_2m_max"],
                    "RH2M": r["daily"]["relative_humidity_2m_mean"],
                    "WS2M": r["daily"]["wind_speed_10m_max"],
                }).fillna(0)

                df["rain_90d_sum"] = df["PRECTOTCORR"].rolling(90).sum()
                df["rain_3d_sum"] = df["PRECTOTCORR"].rolling(3).sum()
                df["rain_7d_sum"] = df["PRECTOTCORR"].rolling(7).sum()
                df["temp_30d_avg"] = df["T2M"].rolling(30).mean()
                df["humid_30d_avg"] = df["RH2M"].rolling(30).mean()
                df["temp_3d_avg"] = df["T2M"].rolling(3).mean()
                df["temp_7d_max"] = df["T2M_MAX"].rolling(7).max()
                df["humid_3d_avg"] = df["RH2M"].rolling(3).mean()

                last = df.iloc[-1]
                month = last["date"].month
                sin_m = np.sin(2 * np.pi * month / 12)
                cos_m = np.cos(2 * np.pi * month / 12)

                # Drought
                d_model, _ = brains["drought"]
                d_in = [last["rain_90d_sum"], last["temp_30d_avg"], last["humid_30d_avg"],
                        last["PRECTOTCORR"], last["RH2M"], last["T2M_MAX"], last["WS2M"], sin_m, cos_m]
                d_prob = d_model.predict_proba([d_in])[0][1] * 100

                # Heatwave
                h_model, _, _ = brains["heatwave"]
                h_in = [last["temp_3d_avg"], last["temp_7d_max"], last["humid_3d_avg"],
                        last["T2M_MAX"], last["T2M"], last["RH2M"], last["WS2M"], sin_m, cos_m]
                h_prob = h_model.predict_proba([h_in])[0][1] * 100
                if last["T2M_MAX"] < 30:
                    h_prob = 0

                # Flood
                f_model, _, _ = brains["flood"]
                f_in = [last["rain_3d_sum"], last["rain_7d_sum"], last["humid_3d_avg"],
                        last["PRECTOTCORR"], last["RH2M"], last["WS2M"], sin_m, cos_m]
                ml_flood = f_model.predict_proba([f_in])[0][1] * 100
                heuristic = np.clip(last["rain_3d_sum"] * 2 + last["rain_7d_sum"] * 0.2 - 10, 0, 100)
                f_prob = max(ml_flood, heuristic)

                st.session_state["results"] = {
                    "d_prob": d_prob, "h_prob": h_prob, "f_prob": f_prob,
                    "features": last.to_dict(),
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                }
            except Exception as e:
                st.error(f"Analysis failed: {e}")

    # ── Results Display ──────────────────────────────────────────────────────
    if "results" in st.session_state:
        res = st.session_state["results"]
        feat = res["features"]
        st.caption(f"Last updated: {res['timestamp']}")

        # Quick-stat row
        qs1, qs2, qs3 = st.columns(3)
        with qs1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Drought</div>
                <div class="metric-value" style="color: {'#f87171' if res['d_prob']>60 else '#fbbf24' if res['d_prob']>30 else '#4ade80'};">
                    {int(res['d_prob'])}%</div>
            </div>""", unsafe_allow_html=True)
        with qs2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Heatwave</div>
                <div class="metric-value" style="color: {'#f87171' if res['h_prob']>60 else '#fbbf24' if res['h_prob']>30 else '#4ade80'};">
                    {int(res['h_prob'])}%</div>
            </div>""", unsafe_allow_html=True)
        with qs3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Flood</div>
                <div class="metric-value" style="color: {'#f87171' if res['f_prob']>60 else '#fbbf24' if res['f_prob']>30 else '#4ade80'};">
                    {int(res['f_prob'])}%</div>
            </div>""", unsafe_allow_html=True)

        st.markdown('<div style="height: 1rem;"></div>', unsafe_allow_html=True)

        # Detailed risk bars
        hazards = [
            ("Drought", res["d_prob"], "drought", "🏜️"),
            ("Heatwave", res["h_prob"], "heatwave", "🔥"),
            ("Flood", res["f_prob"], "flood", "🌊"),
        ]

        for title, prob, htype, icon in hazards:
            impact_text, css_class = get_impact_level(prob)

            st.markdown(f"""
            <div class="risk-bar">
                <div class="rb-left">
                    <span class="rb-icon">{icon}</span>
                    <div>
                        <div class="rb-name">{title}</div>
                        <div class="rb-sub">{int(prob)}% probability</div>
                    </div>
                </div>
                <span class="rb-badge {css_class}">{impact_text}</span>
            </div>""", unsafe_allow_html=True)

            with st.expander(f"Details & actions for {title}", expanded=(prob > 60)):
                reasons = generate_explanation(htype, feat, prob)
                if reasons:
                    for reason in reasons:
                        st.markdown(f"- {reason}")
                else:
                    st.markdown("Conditions are within normal bounds.")

                # Key metrics
                mc1, mc2, mc3 = st.columns(3)
                if htype == "drought":
                    mc1.metric("90-Day Rain", f"{feat['rain_90d_sum']:.1f} mm")
                    mc2.metric("Avg Temp (30d)", f"{feat['temp_30d_avg']:.1f} °C")
                    mc3.metric("Humidity (30d)", f"{feat['humid_30d_avg']:.1f} %")
                elif htype == "heatwave":
                    mc1.metric("Max Temp", f"{feat['T2M_MAX']:.1f} °C")
                    mc2.metric("3-Day Avg", f"{feat['temp_3d_avg']:.1f} °C")
                    mc3.metric("Humidity (3d)", f"{feat['humid_3d_avg']:.1f} %")
                elif htype == "flood":
                    mc1.metric("3-Day Precip", f"{feat['rain_3d_sum']:.1f} mm")
                    mc2.metric("7-Day Total", f"{feat['rain_7d_sum']:.1f} mm")
                    mc3.metric("Wind", f"{feat['WS2M']:.0f} km/h")

                if prob > 20:
                    if st.button(f"Get {title} Relief Plan →", key=f"btn_{htype}", use_container_width=True):
                        st.session_state["teleport_loc"] = st.session_state["location_name"]
                        st.session_state["teleport_dis"] = title
                        st.switch_page("pages/1_Relief_Brain.py")

        # AI Hazard Briefing
        feat_summary = (
            f"- 90-day rain: {feat['rain_90d_sum']:.0f} mm\n"
            f"- 30-day avg temp: {feat['temp_30d_avg']:.1f}°C\n"
            f"- Max temp today: {feat['T2M_MAX']:.1f}°C\n"
            f"- 3-day rain: {feat['rain_3d_sum']:.0f} mm\n"
            f"- 7-day rain: {feat['rain_7d_sum']:.0f} mm\n"
            f"- Humidity (3d avg): {feat['humid_3d_avg']:.0f}%\n"
            f"- Wind: {feat['WS2M']:.0f} km/h"
        )
        briefing = ai_hazard_briefing(
            st.session_state['location_name'],
            res['d_prob'], res['h_prob'], res['f_prob'], feat_summary
        )
        if briefing:
            st.markdown("""
            <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                        letter-spacing: 0.5px; color: #64748b; margin: 1rem 0 0.5rem;">
                AI Hazard Briefing</div>
            """, unsafe_allow_html=True)
            st.markdown(f'<div class="glass-card" style="border-left: 3px solid #6366f1;">{briefing}</div>', unsafe_allow_html=True)