import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from utils.ui import inject_global_css, render_sidebar, page_header
from utils.gemini import ai_weather_narrative

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Weather Intel — AgroSync", page_icon="🌦️", layout="wide")
inject_global_css()


# ── Weather API ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=1800)
def fetch_weather(lat: float, lon: float) -> dict | None:
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
        "precipitation_probability_max,relative_humidity_2m_mean,"
        "wind_speed_10m_max,uv_index_max,weathercode"
        "&hourly=temperature_2m,precipitation"
        "&past_days=7&forecast_days=7&timezone=auto"
    )
    try:
        data = requests.get(url, timeout=15).json()
        if "daily" not in data:
            return None
        return data
    except Exception:
        return None


WMO_CODES = {
    0: ("Clear sky", "☀️"), 1: ("Mostly clear", "🌤️"), 2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"), 45: ("Fog", "🌫️"), 48: ("Rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"), 53: ("Drizzle", "🌦️"), 55: ("Dense drizzle", "🌧️"),
    61: ("Light rain", "🌦️"), 63: ("Rain", "🌧️"), 65: ("Heavy rain", "🌧️"),
    71: ("Light snow", "🌨️"), 73: ("Snow", "🌨️"), 75: ("Heavy snow", "❄️"),
    80: ("Rain showers", "🌦️"), 81: ("Moderate showers", "🌧️"), 82: ("Violent showers", "⛈️"),
    95: ("Thunderstorm", "⛈️"), 96: ("Thunderstorm + hail", "⛈️"), 99: ("Severe storm", "🌪️"),
}


# ── Agricultural weather alerts ──────────────────────────────────────────────
def generate_ag_alerts(daily_df: pd.DataFrame) -> list[dict]:
    alerts = []
    forecast = daily_df[daily_df["date"] >= datetime.now().strftime("%Y-%m-%d")]

    for _, day in forecast.iterrows():
        date_str = pd.to_datetime(day["date"]).strftime("%a %b %d")

        # Heat alert
        if day["temp_max"] > 40:
            alerts.append({
                "level": "danger", "date": date_str,
                "title": "Extreme Heat Warning",
                "msg": f"Max temperature {day['temp_max']:.0f}°C. Irrigate early morning. Provide shade for young transplants.",
            })
        elif day["temp_max"] > 35:
            alerts.append({
                "level": "warn", "date": date_str,
                "title": "Heat Advisory",
                "msg": f"High temperature {day['temp_max']:.0f}°C expected. Avoid fertilizer application mid-day.",
            })

        # Heavy rain alert
        if day["precip"] > 50:
            alerts.append({
                "level": "danger", "date": date_str,
                "title": "Heavy Rain Warning",
                "msg": f"Expected {day['precip']:.0f} mm. Risk of waterlogging and nutrient runoff. Ensure drainage.",
            })
        elif day["precip"] > 20:
            alerts.append({
                "level": "warn", "date": date_str,
                "title": "Rain Alert",
                "msg": f"Moderate rain ({day['precip']:.0f} mm). Skip irrigation. Delay pesticide spraying.",
            })

        # Frost risk
        if day["temp_min"] < 4:
            alerts.append({
                "level": "danger", "date": date_str,
                "title": "Frost Risk",
                "msg": f"Min temp {day['temp_min']:.0f}°C. Cover sensitive crops. Irrigate evening before to retain soil warmth.",
            })

        # Wind alert
        if day["wind"] > 40:
            alerts.append({
                "level": "warn", "date": date_str,
                "title": "High Wind Advisory",
                "msg": f"Winds up to {day['wind']:.0f} km/h. Secure shade nets, stakes, and greenhouse covers.",
            })

        # UV alert
        if day.get("uv") and day["uv"] > 10:
            alerts.append({
                "level": "warn", "date": date_str,
                "title": "High UV Index",
                "msg": "Extreme UV exposure. Field workers should wear protection. Young crops may suffer leaf burn.",
            })

    return alerts


# ── Farming calendar insights ────────────────────────────────────────────────
def get_farming_window(daily_df: pd.DataFrame) -> dict:
    forecast = daily_df[daily_df["date"] >= datetime.now().strftime("%Y-%m-%d")]
    if forecast.empty:
        return {}

    dry_streak = 0
    best_spray_days = []
    irrigation_skip_days = []

    for _, day in forecast.iterrows():
        date_str = pd.to_datetime(day["date"]).strftime("%a %b %d")
        if day["precip"] < 2:
            dry_streak += 1
            if day["wind"] < 15 and day["temp_max"] < 35:
                best_spray_days.append(date_str)
        else:
            dry_streak = 0
            irrigation_skip_days.append(date_str)

    return {
        "spray_days": best_spray_days[:3],
        "skip_irrigation": irrigation_skip_days[:3],
        "dry_streak": dry_streak,
    }


# ── Main UI ──────────────────────────────────────────────────────────────────
def main():
    render_sidebar("Weather Intel")

    lat = st.session_state.get("lat", 12.9716)
    lon = st.session_state.get("lon", 77.5946)
    loc_name = st.session_state.get("location_name", "Bengaluru")

    page_header("Weather Intelligence", f"Agricultural weather insights for {loc_name}")

    data = fetch_weather(lat, lon)
    if not data:
        st.error("Could not fetch weather data. Check your connection.")
        return

    daily = data["daily"]
    daily_df = pd.DataFrame({
        "date": daily["time"],
        "temp_max": daily["temperature_2m_max"],
        "temp_min": daily["temperature_2m_min"],
        "precip": daily["precipitation_sum"],
        "rain_prob": daily.get("precipitation_probability_max", [0] * len(daily["time"])),
        "humidity": daily["relative_humidity_2m_mean"],
        "wind": daily["wind_speed_10m_max"],
        "uv": daily.get("uv_index_max", [0] * len(daily["time"])),
        "code": daily.get("weathercode", [0] * len(daily["time"])),
    })

    # ── 7-day forecast cards ─────────────────────────────────────────────
    st.markdown("""
    <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.5px; color: #64748b; margin-bottom: 0.5rem;">
        7-Day Forecast</div>
    """, unsafe_allow_html=True)
    forecast_df = daily_df[daily_df["date"] >= datetime.now().strftime("%Y-%m-%d")].head(7)

    # AI Weather Briefing
    forecast_summary = "\n".join(
        f"- {pd.to_datetime(row['date']).strftime('%a %b %d')}: {row['temp_max']:.0f}°C/{row['temp_min']:.0f}°C, "
        f"{row['precip']:.0f}mm rain, {row['humidity']:.0f}% humidity, {row['wind']:.0f}km/h wind"
        for _, row in forecast_df.iterrows()
    )
    alerts = generate_ag_alerts(daily_df)
    alerts_text = "\n".join(f"- {a['date']}: {a['title']} — {a['msg']}" for a in alerts) if alerts else "No alerts."
    narrative = ai_weather_narrative(loc_name, forecast_summary, alerts_text)
    if narrative:
        st.markdown(f'<div class="glass-card" style="border-left: 3px solid #6366f1;">{narrative}</div>', unsafe_allow_html=True)
        st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)

    cols = st.columns(min(len(forecast_df), 7))

    for i, (_, day) in enumerate(forecast_df.iterrows()):
        if i >= len(cols):
            break
        code = int(day["code"]) if pd.notna(day["code"]) else 0
        desc, icon = WMO_CODES.get(code, ("Unknown", "🌡️"))
        day_name = pd.to_datetime(day["date"]).strftime("%a")

        with cols[i]:
            st.markdown(f"""
            <div class="metric-card" style="padding: 1rem 0.5rem;">
                <div class="metric-label">{day_name}</div>
                <div style="font-size: 1.8rem; margin: 0.3rem 0;">{icon}</div>
                <div class="metric-value" style="font-size: 1.3rem;">
                    {day['temp_max']:.0f}°<span style="color:#64748b;font-size:0.9rem;">/{day['temp_min']:.0f}°</span>
                </div>
                <div class="metric-sub">{day['precip']:.0f} mm · {day['humidity']:.0f}%</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Agricultural alerts ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.5px; color: #64748b; margin-bottom: 0.5rem;">
        Agricultural Weather Alerts</div>
    """, unsafe_allow_html=True)
    alerts = generate_ag_alerts(daily_df)

    if not alerts:
        st.markdown("""
        <div class="glass-card" style="border-left: 3px solid #4ade80;">
            No weather alerts. Conditions are favorable for field operations.
        </div>""", unsafe_allow_html=True)
    else:
        for alert in alerts:
            border_color = "#f87171" if alert["level"] == "danger" else "#fbbf24"
            st.markdown(f"""
            <div class="glass-card" style="border-left: 3px solid {border_color};">
                <strong>{alert['date']} — {alert['title']}</strong><br>
                <span style="color: #94a3b8;">{alert['msg']}</span>
            </div>
            """, unsafe_allow_html=True)

    # ── Farming windows ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.5px; color: #64748b; margin-bottom: 0.5rem;">
        Optimal Farming Windows</div>
    """, unsafe_allow_html=True)
    windows = get_farming_window(daily_df)

    wc1, wc2, wc3 = st.columns(3)
    with wc1:
        st.markdown("**Best Spray Days**")
        if windows.get("spray_days"):
            for d in windows["spray_days"]:
                st.success(d)
        else:
            st.info("No ideal spray days in forecast")

    with wc2:
        st.markdown("**Skip Irrigation**")
        if windows.get("skip_irrigation"):
            for d in windows["skip_irrigation"]:
                st.warning(d)
        else:
            st.info("No significant rain — irrigate normally")

    with wc3:
        st.markdown("**Dry Stretch**")
        streak = windows.get("dry_streak", 0)
        if streak >= 5:
            st.error(f"{streak} consecutive dry days — monitor soil moisture")
        elif streak >= 3:
            st.warning(f"{streak} dry days ahead")
        else:
            st.success("Adequate moisture expected")

    # ── Detailed data table ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.5px; color: #64748b; margin-bottom: 0.5rem;">
        Detailed Forecast Data</div>
    """, unsafe_allow_html=True)
    display = daily_df.copy()
    display["date"] = pd.to_datetime(display["date"]).dt.strftime("%a %b %d")
    display = display.rename(columns={
        "date": "Date", "temp_max": "High °C", "temp_min": "Low °C",
        "precip": "Rain mm", "rain_prob": "Rain %", "humidity": "Humidity %",
        "wind": "Wind km/h", "uv": "UV Index",
    })
    display = display.drop(columns=["code"], errors="ignore")
    st.dataframe(display, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
