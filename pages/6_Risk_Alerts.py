import streamlit as st
import pandas as pd
import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from utils.ui import inject_global_css, render_sidebar, page_header
from utils.gemini import ai_risk_summary

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Risk Alerts — AgroSync", page_icon="🚨", layout="wide")
inject_global_css()

ALERT_STATE_FILE = "data/state/alert_state.json"


# ── Weather fetch ────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=1800)
def fetch_risk_weather(lat: float, lon: float) -> dict | None:
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
        "relative_humidity_2m_mean,wind_speed_10m_max"
        "&past_days=30&forecast_days=7&timezone=auto"
    )
    try:
        data = requests.get(url, timeout=15).json()
        if "daily" not in data:
            return None
        return data
    except Exception:
        return None


# ── Crop disease risk engine ─────────────────────────────────────────────────
DISEASE_CONDITIONS = {
    "Blast (Rice)": {
        "crops": ["rice", "paddy"],
        "conditions": lambda h, t: h > 85 and 25 <= t <= 30,
        "advice": "Apply tricyclazole or isoprothiolane sprays. Avoid excess nitrogen.",
    },
    "Brown Spot": {
        "crops": ["rice", "paddy", "wheat"],
        "conditions": lambda h, t: h > 80 and 25 <= t <= 32,
        "advice": "Improve nutrition (potassium). Apply mancozeb or copper oxychloride.",
    },
    "Powdery Mildew": {
        "crops": ["wheat", "vegetables", "tomato"],
        "conditions": lambda h, t: 60 <= h <= 80 and 20 <= t <= 28,
        "advice": "Apply sulfur-based fungicide. Improve air circulation.",
    },
    "Late Blight (Tomato/Potato)": {
        "crops": ["tomato", "vegetables", "potato"],
        "conditions": lambda h, t: h > 85 and 15 <= t <= 22,
        "advice": "Spray metalaxyl + mancozeb immediately. Remove infected plants.",
    },
    "Rust (Wheat/Sugarcane)": {
        "crops": ["wheat", "sugarcane"],
        "conditions": lambda h, t: h > 70 and 15 <= t <= 25,
        "advice": "Apply propiconazole fungicide. Use resistant varieties next season.",
    },
    "Bollworm (Cotton)": {
        "crops": ["cotton"],
        "conditions": lambda h, t: h < 60 and t > 30,
        "advice": "Scout fields regularly. Use pheromone traps and Bt sprays.",
    },
    "Downy Mildew (Millet)": {
        "crops": ["millet", "bajra", "ragi"],
        "conditions": lambda h, t: h > 85 and 20 <= t <= 28,
        "advice": "Treat seeds with metalaxyl before sowing. Remove infected plants.",
    },
}


def assess_disease_risk(humidity: float, temp_max: float, crop: str) -> list[dict]:
    """Check current conditions against known disease triggers."""
    crop_lower = crop.lower()
    risks = []
    for disease, info in DISEASE_CONDITIONS.items():
        crop_match = any(c in crop_lower for c in info["crops"])
        if crop_match and info["conditions"](humidity, temp_max):
            risks.append({
                "disease": disease,
                "advice": info["advice"],
                "level": "critical",
            })
        elif crop_match:
            risks.append({
                "disease": disease,
                "advice": info["advice"],
                "level": "low",
            })
    return risks


# ── Market price drop detection (rule-based) ────────────────────────────────
def assess_market_risks(month: int) -> list[dict]:
    """Flag crops likely to face price drops based on harvest season gluts."""
    risks = []

    glut_map = {
        (10, 11, 12): [("Rice", "Kharif rice harvest floods the market. Consider storage."),
                       ("Soybean", "Post-harvest soybean supply surge. Early sellers fare better.")],
        (3, 4, 5): [("Wheat", "Rabi wheat harvest creates supply glut. Store for 2-3 months."),
                    ("Onion", "Late rabi onion harvest. Prices may dip before monsoon spike.")],
        (1, 2, 3): [("Tomato", "Winter tomato supply peaks. Prices may drop."),
                    ("Vegetables", "High winter vegetable production depresses some prices.")],
        (7, 8, 9): [("Cotton", "Raw cotton prices may dip pre-harvest as spinners wait.")],
    }

    for months, items in glut_map.items():
        if month in months:
            for crop, msg in items:
                risks.append({"crop": crop, "msg": msg, "level": "warning"})

    return risks


# ── Composite risk score ─────────────────────────────────────────────────────
def compute_risk_score(weather_alerts: list, disease_risks: list, market_risks: list) -> int:
    score = 0
    for a in weather_alerts:
        score += 20 if a["level"] == "critical" else 10
    for d in disease_risks:
        score += 15 if d["level"] == "critical" else 0
    for m in market_risks:
        score += 10
    return min(score, 100)


# ── Weather risk analysis ───────────────────────────────────────────────────
def assess_weather_risks(daily_df: pd.DataFrame) -> list[dict]:
    alerts = []
    forecast = daily_df[daily_df["date"] >= datetime.now().strftime("%Y-%m-%d")]

    # Drought check (past 30 days)
    past = daily_df[daily_df["date"] < datetime.now().strftime("%Y-%m-%d")]
    if not past.empty:
        rain_30d = past["precip"].sum()
        if rain_30d < 20:
            alerts.append({
                "level": "critical",
                "title": "Drought Risk",
                "msg": f"Only {rain_30d:.0f} mm rain in the last 30 days. Severe moisture deficit.",
                "action": "Start conservation irrigation. Consider drought-tolerant crop varieties.",
            })
        elif rain_30d < 50:
            alerts.append({
                "level": "warning",
                "title": "Below-Average Rainfall",
                "msg": f"{rain_30d:.0f} mm in 30 days — below typical requirements.",
                "action": "Monitor soil moisture. Prepare supplemental irrigation.",
            })

    for _, day in forecast.iterrows():
        date_str = pd.to_datetime(day["date"]).strftime("%a %b %d")

        if day["temp_max"] > 42:
            alerts.append({
                "level": "critical", "title": f"Extreme Heat — {date_str}",
                "msg": f"Temp may reach {day['temp_max']:.0f}°C. Crop stress likely.",
                "action": "Irrigate at dawn. Apply mulch. Consider shade nets for vegetables.",
            })

        if day["precip"] > 60:
            alerts.append({
                "level": "critical", "title": f"Flood Risk — {date_str}",
                "msg": f"Heavy rainfall ({day['precip']:.0f} mm) expected.",
                "action": "Clear drainage channels. Do not apply fertilizer. Secure harvested produce.",
            })

        if day["wind"] > 50:
            alerts.append({
                "level": "critical", "title": f"Storm Warning — {date_str}",
                "msg": f"Winds up to {day['wind']:.0f} km/h.",
                "action": "Harvest mature crops immediately. Secure structures and equipment.",
            })

        if day["temp_min"] < 2:
            alerts.append({
                "level": "critical", "title": f"Frost Warning — {date_str}",
                "msg": f"Min temp {day['temp_min']:.0f}°C — frost likely.",
                "action": "Cover sensitive crops. Irrigate the evening before to retain soil heat.",
            })

    return alerts


# ── Alert persistence ───────────────────────────────────────────────────────
def load_alert_state() -> dict:
    if os.path.exists(ALERT_STATE_FILE):
        try:
            with open(ALERT_STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_check": None, "dismissed": []}


def save_alert_state(state: dict):
    os.makedirs(os.path.dirname(ALERT_STATE_FILE), exist_ok=True)
    with open(ALERT_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ── Main UI ──────────────────────────────────────────────────────────────────
def main():
    render_sidebar("Risk Alerts")

    with st.sidebar:
        st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)
        crop = st.selectbox("Your Crop", [
            "Rice/Paddy", "Wheat", "Millet (Bajra)", "Tomato/Vegetables",
            "Cotton", "Sugarcane", "Soybean", "Groundnut",
        ])

    lat = st.session_state.get("lat", 12.9716)
    lon = st.session_state.get("lon", 77.5946)
    loc_name = st.session_state.get("location_name", "Bengaluru")

    page_header("Risk Alerts", f"Comprehensive risk monitoring for {loc_name}")

    # Fetch data
    data = fetch_risk_weather(lat, lon)
    if not data:
        st.error("Could not fetch weather data.")
        return

    daily = data["daily"]
    daily_df = pd.DataFrame({
        "date": daily["time"],
        "temp_max": daily["temperature_2m_max"],
        "temp_min": daily["temperature_2m_min"],
        "precip": daily["precipitation_sum"],
        "humidity": daily["relative_humidity_2m_mean"],
        "wind": daily["wind_speed_10m_max"],
    })

    # Run all risk engines
    weather_alerts = assess_weather_risks(daily_df)
    today_weather = daily_df[daily_df["date"] >= datetime.now().strftime("%Y-%m-%d")].iloc[0] if not daily_df.empty else None
    disease_risks = []
    if today_weather is not None:
        disease_risks = assess_disease_risk(today_weather["humidity"], today_weather["temp_max"], crop)
    market_risks = assess_market_risks(datetime.now().month)

    # Composite score
    risk_score = compute_risk_score(weather_alerts, disease_risks, market_risks)

    # Header metrics
    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        color = "#f87171" if risk_score > 60 else "#fbbf24" if risk_score > 30 else "#4ade80"
        label = "Critical" if risk_score > 60 else "Moderate" if risk_score > 30 else "Low"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Risk Score</div>
            <div class="metric-value" style="color: {color};">{risk_score}</div>
            <div class="metric-sub" style="color: {color};">{label}</div>
        </div>""", unsafe_allow_html=True)
    with sc2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Weather Alerts</div>
            <div class="metric-value">{len(weather_alerts)}</div>
        </div>""", unsafe_allow_html=True)
    with sc3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Disease Risks</div>
            <div class="metric-value">{sum(1 for d in disease_risks if d['level'] == 'critical')}</div>
        </div>""", unsafe_allow_html=True)
    with sc4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Market Warnings</div>
            <div class="metric-value">{len(market_risks)}</div>
        </div>""", unsafe_allow_html=True)

    # AI Risk Intelligence Briefing
    weather_str = "\n".join(f"- {a['title']}: {a['msg']}" for a in weather_alerts) if weather_alerts else "No weather alerts."
    disease_str = "\n".join(f"- {d['disease']} ({d['level']}): {d['advice']}" for d in disease_risks if d['level'] == 'critical') if disease_risks else "No active disease risks."
    market_str = "\n".join(f"- {m['crop']}: {m['msg']}" for m in market_risks) if market_risks else "No market warnings."
    ai_briefing = ai_risk_summary(loc_name, risk_score, weather_str, disease_str, market_str)
    if ai_briefing:
        st.markdown("""
        <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                    letter-spacing: 0.5px; color: #64748b; margin: 1rem 0 0.5rem;">
            AI Risk Intelligence</div>
        """, unsafe_allow_html=True)
        st.markdown(f'<div class="glass-card" style="border-left: 3px solid #6366f1;">{ai_briefing}</div>', unsafe_allow_html=True)

    # ── Weather Alerts ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.5px; color: #64748b; margin-bottom: 0.5rem;">
        Weather Alerts</div>
    """, unsafe_allow_html=True)
    if weather_alerts:
        for alert in weather_alerts:
            border_color = "#f87171" if alert["level"] == "critical" else "#fbbf24"
            st.markdown(f"""
            <div class="glass-card" style="border-left: 3px solid {border_color};">
                <div style="font-weight: 600;">{alert['title']}</div>
                <div style="font-size: 0.88rem; color: #94a3b8; margin-top: 0.2rem;">{alert['msg']}</div>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("Recommended action"):
                st.markdown(alert["action"])
    else:
        st.markdown("""
        <div class="glass-card" style="border-left: 3px solid #4ade80;">
            <div style="font-weight: 600;">All Clear</div>
            <div style="font-size: 0.88rem; color: #94a3b8;">No severe weather alerts for the next 7 days.</div>
        </div>""", unsafe_allow_html=True)

    # ── Disease Alerts ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.5px; color: #64748b; margin-bottom: 0.5rem;">
        Crop Disease Alerts</div>
    """, unsafe_allow_html=True)
    st.caption(f"Based on current conditions for {crop}")

    active_diseases = [d for d in disease_risks if d["level"] == "critical"]
    if active_diseases:
        for d in active_diseases:
            st.markdown(f"""
            <div class="glass-card" style="border-left: 3px solid #f87171;">
                <div style="font-weight: 600;">{d['disease']} — Active Risk</div>
                <div style="font-size: 0.88rem; color: #94a3b8; margin-top: 0.2rem;">{d['advice']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="glass-card" style="border-left: 3px solid #4ade80;">
            <div style="font-weight: 600;">Low Disease Risk</div>
            <div style="font-size: 0.88rem; color: #94a3b8;">Current conditions don't favor major outbreaks.</div>
        </div>""", unsafe_allow_html=True)

    # ── Market Alerts ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.5px; color: #64748b; margin-bottom: 0.5rem;">
        Market Price Alerts</div>
    """, unsafe_allow_html=True)
    if market_risks:
        for m in market_risks:
            st.markdown(f"""
            <div class="glass-card" style="border-left: 3px solid #fbbf24;">
                <div style="font-weight: 600;">{m['crop']} — Price Pressure</div>
                <div style="font-size: 0.88rem; color: #94a3b8; margin-top: 0.2rem;">{m['msg']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="glass-card" style="border-left: 3px solid #60a5fa;">
            <div style="font-weight: 600;">Stable Market</div>
            <div style="font-size: 0.88rem; color: #94a3b8;">No significant price drop warnings for this period.</div>
        </div>""", unsafe_allow_html=True)

    # Save state
    state = load_alert_state()
    state["last_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_alert_state(state)
    st.caption(f"Last checked: {state['last_check']}")


if __name__ == "__main__":
    main()
