import streamlit as st
import pandas as pd
import requests
import os
from duckduckgo_search import DDGS
from datetime import datetime
from dotenv import load_dotenv
from utils.ui import inject_global_css, render_sidebar, page_header
from utils.gemini import ai_crop_doctor, ai_tactical_briefing

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Tactical AI — AgroSync", page_icon="🧠", layout="wide")
inject_global_css()


# ── Crop knowledge base ─────────────────────────────────────────────────────
CROP_PROFILES = {
    "Millet (Drought Resistant)": {
        "water_need": "low",
        "context": "Millet uses ~70% less water than rice. Avoid overwatering.",
        "fert_note": "Light NPK application during tillering stage.",
        "disease_crops": ["downy mildew", "rust"],
    },
    "Rice/Paddy": {
        "water_need": "high",
        "context": "Rice needs standing water or very high soil moisture. Keep field bunds secure.",
        "fert_note": "Split nitrogen applications — basal + top-dressing at tillering and panicle stages.",
        "disease_crops": ["blast", "brown spot", "bacterial leaf blight"],
    },
    "Wheat": {
        "water_need": "medium",
        "context": "Wheat needs critical irrigation at crown root, tillering, flowering, and grain filling stages.",
        "fert_note": "Apply full phosphorus and potassium at sowing; split nitrogen at sowing and first irrigation.",
        "disease_crops": ["rust", "powdery mildew", "karnal bunt"],
    },
    "Tomato/Vegetables": {
        "water_need": "medium",
        "context": "Consistent moisture is key — irregular watering causes blossom end rot and fruit cracking.",
        "fert_note": "Balanced NPK with extra calcium. Side-dress every 3-4 weeks after transplant.",
        "disease_crops": ["early blight", "late blight", "fusarium wilt"],
    },
    "Sugarcane": {
        "water_need": "high",
        "context": "Sugarcane is water-intensive. Drip irrigation saves up to 40% water vs. flood irrigation.",
        "fert_note": "Heavy nitrogen requirement, apply in 3 splits. Add potassium for sucrose accumulation.",
        "disease_crops": ["red rot", "smut", "grassy shoot disease"],
    },
    "Cotton": {
        "water_need": "medium",
        "context": "Cotton is sensitive to waterlogging. Ensure good drainage after heavy rain.",
        "fert_note": "Moderate nitrogen; excess causes vegetative growth at the expense of bolls.",
        "disease_crops": ["bollworm", "whitefly", "bacterial blight"],
    },
}

# ── Soil drainage characteristics ────────────────────────────────────────────
SOIL_DRAINAGE = {
    "sandy": ("fast", "Water more frequently in smaller amounts — sandy soil drains very fast."),
    "alluvial": ("moderate", "Good water-holding capacity. Standard irrigation schedules work well."),
    "black": ("slow", "Clay-heavy soil holds water tightly. Be careful not to overwater — risk of root rot."),
    "clay": ("slow", "Drains slowly. Reduce irrigation frequency; allow topsoil to dry between waterings."),
    "red": ("moderate", "Moderate drainage. Benefits from organic mulching to retain moisture."),
    "laterite": ("fast", "Porous soil loses nutrients quickly. Pair irrigation with mulching."),
    "loamy": ("ideal", "Excellent balance of drainage and retention. Ideal for most crops."),
}


# ── Soil type auto-detection ─────────────────────────────────────────────────
SOIL_REGION_MAP = {
    "Red Soil": ["karnataka", "bengaluru", "tamil nadu"],
    "Black Soil (Regur)": ["maharashtra", "gujarat", "madhya pradesh"],
    "Alluvial Soil": ["punjab", "up", "bihar"],
    "Laterite Soil": ["madagascar"],
    "Clay Soil": ["texas"],
    "Sandy Soil": ["florida"],
}


@st.cache_data(show_spinner=False, ttl=86400)
def detect_soil_type(location: str) -> str:
    loc = location.lower()
    for soil_type, keywords in SOIL_REGION_MAP.items():
        if any(kw in loc for kw in keywords):
            return soil_type

    # Fallback: web search
    try:
        ddgs = DDGS()
        results = list(ddgs.text(f"primary agricultural soil type in {location}", max_results=3))
        text = " ".join(r.get("body", "").lower() for r in results)
        for keyword in ["alluvial", "black", "regur", "laterite", "clay", "sandy", "red", "loam"]:
            if keyword in text:
                for soil_name in SOIL_DRAINAGE:
                    if keyword in soil_name or keyword in soil_name:
                        return f"{keyword.title()} Soil"
                return f"{keyword.title()} Soil"
    except Exception:
        pass
    return "Loamy Soil"


# ── Weather API ──────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def fetch_forecast(lat: float, lon: float) -> pd.DataFrame | None:
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
        "relative_humidity_2m_mean,wind_speed_10m_max&timezone=auto"
    )
    try:
        data = requests.get(url, timeout=15).json()
        if "daily" not in data:
            return None
        return pd.DataFrame({
            "date": pd.to_datetime(data["daily"]["time"]),
            "temp_max": data["daily"]["temperature_2m_max"],
            "temp_min": data["daily"]["temperature_2m_min"],
            "precip": data["daily"]["precipitation_sum"],
            "humidity": data["daily"]["relative_humidity_2m_mean"],
            "wind": data["daily"]["wind_speed_10m_max"],
        })
    except Exception:
        return None


# ── Tactical Decision Engine ─────────────────────────────────────────────────
def generate_actions(df: pd.DataFrame, crop: str, soil: str) -> dict:
    profile = CROP_PROFILES.get(crop, CROP_PROFILES["Wheat"])
    today = df.iloc[0]
    tomorrow = df.iloc[1]
    next_3 = df.iloc[1:4]

    actions = {"crop_context": profile["context"]}

    # ── Irrigation ───────────────────────────────────────────────────────
    if tomorrow["precip"] > 10:
        irr_status = "Skip Watering"
        irr_advice = f"Heavy rain ({tomorrow['precip']:.0f} mm) expected tomorrow. Let nature irrigate."
        irr_level = "stop"
    elif today["temp_max"] > 35 and today["precip"] < 2:
        irr_status = "Deep Irrigation Needed"
        irr_advice = "Extreme heat today. Water deeply before 8 AM or after 5 PM to reduce evaporation."
        irr_level = "urgent"
    elif profile["water_need"] == "low":
        irr_status = "Minimal Watering"
        irr_advice = "Conditions normal. Maintain light soil moisture — this crop doesn't need much."
        irr_level = "ok"
    elif profile["water_need"] == "high" and today["precip"] < 5:
        irr_status = "Maintain Standing Water"
        irr_advice = "Low rainfall and high crop water demand. Ensure paddies have 3-5 cm standing water."
        irr_level = "urgent"
    else:
        irr_status = "Standard Watering"
        irr_advice = "Conditions stable. Proceed with your normal drip or sprinkler schedule."
        irr_level = "ok"

    # Soil modifier
    soil_key = None
    for key in SOIL_DRAINAGE:
        if key in soil.lower():
            soil_key = key
            break
    if soil_key:
        _, soil_note = SOIL_DRAINAGE[soil_key]
        irr_advice += f"\n\n*Soil note:* {soil_note}"

    actions["irrigation"] = {"status": irr_status, "advice": irr_advice, "level": irr_level}

    # ── Fertilizer ───────────────────────────────────────────────────────
    rain_3d = next_3["precip"].sum()
    if rain_3d > 25:
        fert_status = "Do Not Apply"
        fert_advice = f"Heavy rain incoming ({rain_3d:.0f} mm in 3 days). Fertilizer will wash away — waste of money."
        fert_level = "stop"
    elif 5 <= rain_3d <= 15:
        fert_status = "Perfect Timing"
        fert_advice = "Light rain expected. Apply top-dressing now — gentle rain pushes nutrients into the root zone."
        fert_level = "ok"
    else:
        fert_status = "Dry Application"
        fert_advice = "No rain expected. If you fertilize today, irrigate immediately after to prevent root burn."
        fert_level = "warn"

    fert_advice += f"\n\n*Crop note:* {profile['fert_note']}"
    actions["fertilizer"] = {"status": fert_status, "advice": fert_advice, "level": fert_level}

    # ── Disease Risk ─────────────────────────────────────────────────────
    fungal = any(
        row["humidity"] > 80 and 25 <= row["temp_max"] <= 32
        for _, row in next_3.iterrows()
    )
    pest_risk = today["temp_max"] > 30 and today["humidity"] < 50

    if fungal:
        dis_status = "High Fungal Risk"
        dis_advice = (
            "Conditions ideal for fungal outbreaks (humidity >80%, temp 25-32 °C). "
            "Apply preventative neem oil or copper fungicide."
        )
        dis_level = "stop"
    elif pest_risk:
        dis_status = "Pest Watch"
        dis_advice = "Hot, dry conditions can increase pest activity. Scout fields for aphids and mites."
        dis_level = "warn"
    else:
        dis_status = "Low Risk"
        dis_advice = "Weather is unfavorable for major outbreaks. Continue standard scouting."
        dis_level = "ok"

    if profile["disease_crops"]:
        dis_advice += f"\n\n*Watch for:* {', '.join(profile['disease_crops'])} (common for {crop})."

    actions["disease"] = {"status": dis_status, "advice": dis_advice, "level": dis_level}

    # ── Harvest Window ───────────────────────────────────────────────────
    dry_days = sum(1 for _, row in next_3.iterrows() if row["precip"] < 2)
    if dry_days >= 3:
        harv_status = "Good Window"
        harv_advice = "Next 3 days are dry — ideal for harvesting and drying produce."
        harv_level = "ok"
    elif dry_days >= 1:
        harv_status = "Partial Window"
        harv_advice = "Some dry days ahead. Prioritize harvesting mature crops on dry days."
        harv_level = "warn"
    else:
        harv_status = "Delay Harvest"
        harv_advice = "Continuous rain expected. Harvesting now risks grain moisture damage."
        harv_level = "stop"
    actions["harvest"] = {"status": harv_status, "advice": harv_advice, "level": harv_level}

    return actions


# ── Crop Doctor Chatbot ──────────────────────────────────────────────────────
SYMPTOM_DB = [
    (["yellow", "chloro"], "**Yellowing Leaves (Chlorosis)**\n\nLikely causes: nitrogen deficiency, iron deficiency, or overwatering.\n\n**Action:** Check soil moisture. If soggy, reduce watering. If dry, apply nitrogen-rich fertilizer (urea) or iron foliar spray."),
    (["brown", "spot"], "**Brown Spots — Likely Fungal Infection**\n\nCould be Brown Spot or Blight.\n\n**Action:** Remove infected leaves. Spray copper-based fungicide or neem oil. Avoid overhead watering."),
    (["white", "powder", "dust", "mildew"], "**Powdery Mildew (Fungal)**\n\n**Action:** Prune affected areas for airflow. Spray sulfur-based fungicide or baking soda + water mix."),
    (["curl", "hole", "chew", "eaten", "bug", "insect"], "**Pest Attack**\n\nLikely aphids, caterpillars, or leaf rollers.\n\n**Action:** Check under leaves for bugs. Apply neem oil or insecticidal soap."),
    (["wilt", "droop", "limp"], "**Wilting / Drooping**\n\nCaused by root rot (overwatering) or severe drought.\n\n**Action:** Dig 2 inches into soil. Wet and smelly = root rot (stop watering). Bone dry = irrigate immediately."),
    (["black", "rot"], "**Black Rot / Stem Rot**\n\nOften caused by soilborne pathogens in waterlogged conditions.\n\n**Action:** Improve drainage, remove affected plants, apply Trichoderma-based biocontrol."),
    (["stunted", "small", "slow"], "**Stunted Growth**\n\nMay indicate phosphorus deficiency, root damage, or compacted soil.\n\n**Action:** Test soil pH and nutrients. Apply DAP fertilizer and loosen soil around roots."),
]


def diagnose(user_input: str) -> str:
    ui = user_input.lower()
    for keywords, response in SYMPTOM_DB:
        if any(kw in ui for kw in keywords):
            return response
    return "I couldn't match your description to a known symptom. Try keywords like: *yellow leaves, brown spots, white powder, curling, wilting, stunted growth*."


# ── Main App ─────────────────────────────────────────────────────────────────
def main():
    # Sidebar
    render_sidebar("Tactical AI")

    with st.sidebar:
        st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
                    letter-spacing: 0.5px; color: #475569; margin-bottom: 0.3rem;">
            Farm Settings</div>
        """, unsafe_allow_html=True)

        default_loc = st.session_state.get("location_name", "Bengaluru")
        lat = st.session_state.get("lat", 12.9716)
        lon = st.session_state.get("lon", 77.5946)

        st.text_input("Farm Location", value=default_loc, disabled=True)
        crop_type = st.selectbox("Current Crop", list(CROP_PROFILES.keys()))

        detected_soil = detect_soil_type(default_loc)
        soil_options = ["Alluvial Soil", "Black Soil (Regur)", "Red Soil", "Laterite Soil",
                        "Clay Soil", "Sandy Soil", "Loamy Soil"]
        soil_idx = soil_options.index(detected_soil) if detected_soil in soil_options else 6
        soil_type = st.selectbox("Soil Type", soil_options, index=soil_idx,
                                 help="Auto-detected from your region. Override if needed.")

    # Header
    page_header("Tactical Farm AI", "Daily actionable instructions for irrigation, fertilizer, disease prevention, and harvest timing.")

    # Fetch weather
    weather_df = fetch_forecast(lat, lon)

    if weather_df is None:
        st.error("Could not fetch weather data. Check your connection.")
        return

    actions = generate_actions(weather_df, crop_type, soil_type)

    # Crop context
    st.markdown(f"""
    <div class="glass-card" style="border-left: 3px solid #4ade80;">
        🌾 <strong>{crop_type}</strong> — {actions["crop_context"]}
    </div>""", unsafe_allow_html=True)

    # AI Tactical Briefing
    today_w = weather_df.iloc[0]
    next_3 = weather_df.iloc[1:4]
    weather_summary = "\n".join(
        f"- {row['date'].strftime('%a')}: {row['temp_max']:.0f}°C/{row['temp_min']:.0f}°C, {row['precip']:.0f}mm rain, {row['humidity']:.0f}% humidity"
        for _, row in next_3.iterrows()
    )
    actions_summary = "\n".join(
        f"- {k.title()}: {v['status']} ({v['level']})"
        for k, v in actions.items() if k != "crop_context"
    )
    briefing = ai_tactical_briefing(weather_summary, crop_type, soil_type, actions_summary)
    if briefing:
        st.markdown("""
        <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                    letter-spacing: 0.5px; color: #64748b; margin: 1rem 0 0.5rem;">
            AI Daily Briefing</div>
        """, unsafe_allow_html=True)
        st.markdown(f'<div class="glass-card" style="border-left: 3px solid #6366f1;">{briefing}</div>', unsafe_allow_html=True)

    # Action cards
    LEVEL_MAP = {"ok": "success", "warn": "warning", "stop": "error", "urgent": "error"}
    ICON_MAP = {"irrigation": "💧", "fertilizer": "🧪", "disease": "🛡️", "harvest": "📦"}
    TITLE_MAP = {"irrigation": "Irrigation", "fertilizer": "Fertilizer", "disease": "Disease Risk", "harvest": "Harvest Window"}

    st.markdown("""
    <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.5px; color: #64748b; margin: 1rem 0 0.5rem;">
        Today's Action Plan</div>
    """, unsafe_allow_html=True)
    cols = st.columns(4)
    for i, key in enumerate(["irrigation", "fertilizer", "disease", "harvest"]):
        act = actions[key]
        with cols[i]:
            icon = ICON_MAP[key]
            title = TITLE_MAP[key]
            level = LEVEL_MAP[act["level"]]
            getattr(st, level)(f"**{icon} {title}**\n\n{act['status']}")
            with st.expander("Details"):
                st.markdown(act["advice"])

    # 7-day forecast table
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.5px; color: #64748b; margin-bottom: 0.5rem;">
        7-Day Weather Outlook</div>
    """, unsafe_allow_html=True)

    display_df = weather_df.copy()
    display_df["date"] = display_df["date"].dt.strftime("%a %b %d")
    display_df = display_df.rename(columns={
        "date": "Date", "temp_max": "High °C", "temp_min": "Low °C",
        "precip": "Rain mm", "humidity": "Humidity %", "wind": "Wind km/h",
    })
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Crop Doctor
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.5px; color: #64748b; margin-bottom: 0.5rem;">
        Crop Doctor</div>
    """, unsafe_allow_html=True)
    st.caption("Describe your plant symptoms for an instant diagnosis.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "What's wrong with your crop? Describe the symptoms (e.g., 'yellow leaves', 'brown spots', 'wilting')."}
        ]

    col_chat, col_clear = st.columns([6, 1])
    with col_clear:
        if st.button("Clear", use_container_width=True):
            st.session_state.chat_history = [
                {"role": "assistant", "content": "Chat cleared. Describe your crop symptoms."}
            ]
            st.rerun()

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_query := st.chat_input("Describe plant symptoms…"):
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Try AI diagnosis first, fall back to keyword matching
        weather_ctx = (
            f"{today_w['temp_max']:.0f}°C max, {today_w['humidity']:.0f}% humidity, {today_w['precip']:.0f}mm rain"
            if weather_df is not None else ""
        )
        with st.spinner("AI analyzing symptoms…"):
            ai_reply = ai_crop_doctor(user_query, crop=crop_type, weather_context=weather_ctx)
        reply = ai_reply if ai_reply else diagnose(user_query)

        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)


if __name__ == "__main__":
    main()