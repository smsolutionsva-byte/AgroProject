import streamlit as st
import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from utils.ui import inject_global_css, render_sidebar, page_header
from utils.gemini import ai_crop_advice

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Crop Advisor — AgroSync", page_icon="🌱", layout="wide")
inject_global_css()


# ── Crop knowledge base ─────────────────────────────────────────────────────
CROP_DB = {
    "Rice": {
        "season": "kharif",
        "months": [6, 7, 8],
        "temp_range": (20, 37),
        "rain_need": "high",
        "soil": ["alluvial", "clay", "loamy"],
        "water": "High — needs standing water",
        "duration": "120-150 days",
        "market": "Staple demand, stable prices",
        "tip": "Best in irrigated lowlands. Transplant seedlings 20-25 days old.",
    },
    "Wheat": {
        "season": "rabi",
        "months": [10, 11, 12],
        "temp_range": (10, 25),
        "rain_need": "low",
        "soil": ["alluvial", "loamy", "clay"],
        "water": "Moderate — 4-6 irrigations",
        "duration": "110-130 days",
        "market": "Government MSP support, consistent demand",
        "tip": "Sow by mid-November for best yield. Delay causes significant yield loss.",
    },
    "Millet (Bajra)": {
        "season": "kharif",
        "months": [6, 7],
        "temp_range": (25, 40),
        "rain_need": "low",
        "soil": ["sandy", "red", "loamy"],
        "water": "Very Low — drought tolerant",
        "duration": "65-80 days",
        "market": "Rising demand, premium health-food prices",
        "tip": "Ideal for dryland farming. Low input cost, good for risk-averse farmers.",
    },
    "Ragi (Finger Millet)": {
        "season": "kharif",
        "months": [5, 6, 7],
        "temp_range": (20, 35),
        "rain_need": "low",
        "soil": ["red", "laterite", "loamy"],
        "water": "Low — rain-fed works well",
        "duration": "90-120 days",
        "market": "Health food trend driving urban demand up",
        "tip": "Excellent for semi-arid regions. Rich in calcium — premium crop.",
    },
    "Tomato": {
        "season": "all",
        "months": list(range(1, 13)),
        "temp_range": (18, 30),
        "rain_need": "medium",
        "soil": ["loamy", "red", "alluvial"],
        "water": "Moderate — consistent drip irrigation",
        "duration": "60-90 days",
        "market": "Volatile but highly profitable during shortage",
        "tip": "Stagger planting every 2-3 weeks for continuous harvest and price arbitrage.",
    },
    "Onion": {
        "season": "rabi",
        "months": [10, 11, 12, 1],
        "temp_range": (15, 30),
        "rain_need": "low",
        "soil": ["alluvial", "loamy", "sandy"],
        "water": "Moderate — stop 10 days before harvest",
        "duration": "100-120 days",
        "market": "Price spikes during monsoon if stored well",
        "tip": "Proper curing and storage can double returns. Sell during May-Aug price spike.",
    },
    "Cotton": {
        "season": "kharif",
        "months": [5, 6, 7],
        "temp_range": (25, 35),
        "rain_need": "medium",
        "soil": ["black", "alluvial", "clay"],
        "water": "Moderate — sensitive to waterlogging",
        "duration": "150-180 days",
        "market": "Export demand drives prices. Sell Oct-Dec.",
        "tip": "Use Bt cotton varieties for bollworm resistance. Maintain good drainage.",
    },
    "Soybean": {
        "season": "kharif",
        "months": [6, 7],
        "temp_range": (20, 35),
        "rain_need": "medium",
        "soil": ["black", "alluvial", "loamy"],
        "water": "Moderate — critical at flowering stage",
        "duration": "90-110 days",
        "market": "Meal and oil demand. Export window Mar-Jun.",
        "tip": "Inoculate seeds with Rhizobium for better nitrogen fixation.",
    },
    "Sugarcane": {
        "season": "all",
        "months": [1, 2, 3, 10],
        "temp_range": (20, 38),
        "rain_need": "high",
        "soil": ["alluvial", "loamy", "black"],
        "water": "Very High — drip saves 40% water",
        "duration": "300-365 days",
        "market": "FRP guaranteed by government",
        "tip": "Plant in February for adsali (18-month) crop or October for suru crop.",
    },
    "Groundnut": {
        "season": "kharif",
        "months": [6, 7],
        "temp_range": (25, 35),
        "rain_need": "medium",
        "soil": ["sandy", "red", "loamy"],
        "water": "Low to Moderate",
        "duration": "100-130 days",
        "market": "Oil and snack demand. Stable market.",
        "tip": "Sandy-loam is ideal. Apply gypsum at flowering for better pod filling.",
    },
}


# ── Recommendation engine ───────────────────────────────────────────────────
def get_current_weather(lat: float, lon: float) -> dict | None:
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        "&daily=temperature_2m_mean,precipitation_sum,relative_humidity_2m_mean"
        "&past_days=30&forecast_days=1&timezone=auto"
    )
    try:
        data = requests.get(url, timeout=15).json()
        if "daily" not in data:
            return None
        temps = [t for t in data["daily"]["temperature_2m_mean"] if t is not None]
        precip = [p for p in data["daily"]["precipitation_sum"] if p is not None]
        return {
            "avg_temp": sum(temps) / len(temps) if temps else 25,
            "total_rain": sum(precip),
            "monthly_rain": sum(precip),
        }
    except Exception:
        return None


def recommend_crops(month: int, soil: str, weather: dict | None) -> list[dict]:
    """Score and rank crops based on current season, soil, and weather."""
    results = []
    soil_key = soil.lower().split()[0] if soil else ""

    for name, info in CROP_DB.items():
        score = 0
        reasons = []

        # Season match (most important)
        if month in info["months"]:
            score += 40
            reasons.append("Optimal sowing season right now")
        elif any(abs(month - m) <= 1 or abs(month - m) >= 11 for m in info["months"]):
            score += 15
            reasons.append("Near sowing window")
        else:
            score += 0
            reasons.append("Off-season — not recommended for sowing")

        # Soil match
        if any(soil_key in s for s in info["soil"]):
            score += 25
            reasons.append(f"Well-suited for {soil} soil")
        else:
            score += 5
            reasons.append(f"Not ideal for {soil} soil — may need amendments")

        # Weather match
        if weather:
            temp = weather["avg_temp"]
            lo, hi = info["temp_range"]
            if lo <= temp <= hi:
                score += 20
                reasons.append(f"Current temp ({temp:.0f}°C) is in optimal range")
            elif lo - 5 <= temp <= hi + 5:
                score += 10
                reasons.append(f"Current temp ({temp:.0f}°C) is marginal")
            else:
                reasons.append(f"Current temp ({temp:.0f}°C) is outside ideal range")

            rain = weather["monthly_rain"]
            if info["rain_need"] == "high" and rain > 100:
                score += 15
                reasons.append("Rainfall supports high-water crops")
            elif info["rain_need"] == "low" and rain < 80:
                score += 15
                reasons.append("Low rainfall suits this drought-tolerant crop")
            elif info["rain_need"] == "medium":
                score += 10

        results.append({
            "name": name,
            "score": min(score, 100),
            "reasons": reasons,
            "info": info,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


# ── Main UI ──────────────────────────────────────────────────────────────────
def main():
    render_sidebar("Crop Advisor")

    page_header("Crop Recommendation", "Get personalized crop suggestions based on your season, soil, and local weather.")

    # Inputs
    c1, c2 = st.columns(2)
    with c1:
        soil = st.selectbox("Soil Type", [
            "Alluvial Soil", "Black Soil", "Red Soil", "Laterite Soil",
            "Clay Soil", "Sandy Soil", "Loamy Soil",
        ])
    with c2:
        month_names = ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November", "December"]
        current_month = datetime.now().month
        selected_month = st.selectbox("Planting Month", month_names, index=current_month - 1)
        month_num = month_names.index(selected_month) + 1

    # Fetch weather for user's location
    lat = st.session_state.get("lat", 12.9716)
    lon = st.session_state.get("lon", 77.5946)
    loc_name = st.session_state.get("location_name", "Bengaluru")

    weather = None
    if st.button("Get Recommendations", type="primary", use_container_width=True):
        with st.spinner("Analyzing local conditions…"):
            weather = get_current_weather(lat, lon)
        st.session_state["crop_weather"] = weather
        st.session_state["crop_results"] = recommend_crops(month_num, soil, weather)

    if "crop_results" in st.session_state:
        results = st.session_state["crop_results"]
        weather = st.session_state.get("crop_weather")

        if weather:
            st.caption(f"Based on: {loc_name} • {weather['avg_temp']:.0f}°C avg • {weather['monthly_rain']:.0f} mm rain (30d)")

        st.markdown("---")

        # Top picks
        st.markdown("""
        <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                    letter-spacing: 0.5px; color: #64748b; margin-bottom: 0.5rem;">
            Top Recommended Crops</div>
        """, unsafe_allow_html=True)
        top = results[:3]
        cols = st.columns(3)
        for i, crop in enumerate(top):
            with cols[i]:
                badge_color = "#4ade80" if crop["score"] >= 60 else "#fbbf24" if crop["score"] >= 35 else "#f87171"
                st.markdown(f"""
                <div class="glass-card" style="border-left: 3px solid {badge_color};">
                    <div style="font-weight: 700; font-size: 1.05rem;">{crop['name']}</div>
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 0.3rem;">
                        Match: <strong style="color: {badge_color};">{crop['score']}%</strong> ·
                        {crop['info']['duration']} · {crop['info']['water']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                for reason in crop["reasons"]:
                    st.markdown(f"- {reason}")

                st.markdown(f"**Strategy:** {crop['info']['tip']}")
                st.markdown(f"**Market:** {crop['info']['market']}")

                # AI Planting Advice for top picks
                weather_str = (
                    f"{weather['avg_temp']:.0f}°C avg temp, {weather['monthly_rain']:.0f}mm rain (30d)"
                    if weather else "Weather data unavailable"
                )
                reasons_str = "\n".join(f"- {r}" for r in crop["reasons"])
                ai_advice = ai_crop_advice(crop["name"], crop["score"], soil, weather_str, reasons_str)
                if ai_advice:
                    st.markdown(f"""
                    <div class="glass-card" style="border-left: 3px solid #6366f1; margin-top: 0.5rem;">
                        <span style="background:#6366f1;color:#fff;font-size:0.65rem;padding:2px 8px;border-radius:999px;">AI Advice</span>
                        <div style="margin-top: 0.5rem;">{ai_advice}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # Full list
        st.markdown("---")
        st.markdown("""
        <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                    letter-spacing: 0.5px; color: #64748b; margin-bottom: 0.5rem;">
            All Crops Ranked</div>
        """, unsafe_allow_html=True)
        for crop in results:
            score = crop["score"]
            label = "Excellent" if score >= 70 else "Good" if score >= 50 else "Fair" if score >= 30 else "Poor"
            with st.expander(f"{crop['name']} — {score}% ({label})"):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Match Score", f"{score}%")
                c2.metric("Season", crop["info"]["season"].title())
                c3.metric("Duration", crop["info"]["duration"])
                c4.metric("Water Need", crop["info"]["water"].split("—")[0].strip())

                for reason in crop["reasons"]:
                    st.markdown(f"- {reason}")
                st.markdown(f"**Tip:** {crop['info']['tip']}")


if __name__ == "__main__":
    main()
