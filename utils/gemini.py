"""Centralized Gemini AI client for AgroSync — provides AI-powered insights across all modules."""
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

_client = None


def _get_client():
    """Lazy-init singleton Gemini client."""
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client


def ai_generate(prompt: str, system_instruction: str = "", max_tokens: int = 2048) -> str | None:
    """Generate text via Gemini. Returns None on failure (graceful degradation)."""
    try:
        from google.genai import types
        client = _get_client()
        full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=max_tokens,
                temperature=0.7,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        return response.text
    except Exception as e:
        # We go full gremlin mode and print the EXACT error to the screen 🚨
        st.error(f"💀 AI BROKE: {e}")
        return None


# ── Specialized AI functions ─────────────────────────────────────────────────

AGRO_SYSTEM = (
    "You are AgroSync AI, an expert agricultural advisor. "
    "Give practical, actionable advice. Use bullet points and bold headers. "
    "Be concise but thorough. Speak directly to the farmer."
)


@st.cache_data(show_spinner=False, ttl=3600)
def ai_relief_plan(location: str, disaster_type: str, region_info: str) -> str | None:
    """Generate an AI-powered disaster relief action plan."""
    prompt = (
        f"Create a step-by-step disaster relief action plan for a farmer in {location} "
        f"affected by {disaster_type}.\n\n"
        f"Regional context:\n{region_info}\n\n"
        "Include:\n"
        "1. Immediate actions (first 48 hours)\n"
        "2. Where to apply for government relief and what documents to prepare\n"
        "3. How to document crop damage for insurance/claims\n"
        "4. Recovery steps to get back to farming\n"
        "5. A pro tip specific to this disaster type and region\n\n"
        "Format with markdown bold headers and bullet points."
    )
    return ai_generate(prompt, AGRO_SYSTEM, max_tokens=1200)


@st.cache_data(show_spinner=False, ttl=3600)
def ai_crop_doctor(symptoms: str, crop: str = "", weather_context: str = "") -> str | None:
    """AI-powered crop disease diagnosis from symptom description."""
    prompt = (
        f"A farmer describes these crop symptoms: \"{symptoms}\"\n"
        + (f"Crop: {crop}\n" if crop else "")
        + (f"Current weather context: {weather_context}\n" if weather_context else "")
        + "\nProvide:\n"
        "1. Most likely diagnosis (disease/deficiency/pest)\n"
        "2. Confidence level (high/medium/low)\n"
        "3. Immediate treatment steps\n"
        "4. Prevention for next season\n"
        "5. When to escalate to an agricultural extension officer\n\n"
        "Keep it practical for a smallholder farmer."
    )
    return ai_generate(prompt, AGRO_SYSTEM, max_tokens=800)


@st.cache_data(show_spinner=False, ttl=3600)
def ai_tactical_briefing(weather_summary: str, crop: str, soil: str, actions_summary: str) -> str | None:
    """Generate an AI tactical daily briefing for the farmer."""
    prompt = (
        f"Generate a concise daily tactical briefing for a farmer.\n\n"
        f"**Crop:** {crop}\n**Soil:** {soil}\n\n"
        f"**Weather (next 3 days):**\n{weather_summary}\n\n"
        f"**System recommendations:**\n{actions_summary}\n\n"
        "Synthesize this into a 3-4 paragraph briefing that:\n"
        "- Prioritizes the most urgent action for today\n"
        "- Explains why in simple terms\n"
        "- Gives a specific time-of-day recommendation\n"
        "- Mentions any upcoming weather changes to prepare for"
    )
    return ai_generate(prompt, AGRO_SYSTEM, max_tokens=600)


@st.cache_data(show_spinner=False, ttl=3600)
def ai_weather_narrative(location: str, forecast_summary: str, alerts_summary: str) -> str | None:
    """Generate a human-readable weather narrative for farmers."""
    prompt = (
        f"Write a brief agricultural weather briefing for {location}.\n\n"
        f"**7-day forecast data:**\n{forecast_summary}\n\n"
        f"**Active alerts:**\n{alerts_summary}\n\n"
        "Write 2-3 paragraphs covering:\n"
        "- Overall weather pattern this week\n"
        "- Key days to watch and why\n"
        "- Specific farming recommendations based on the weather\n"
        "Speak as a trusted agricultural meteorologist."
    )
    return ai_generate(prompt, AGRO_SYSTEM, max_tokens=600)


@st.cache_data(show_spinner=False, ttl=3600)
def ai_risk_summary(location: str, risk_score: int, weather_alerts: str,
                    disease_risks: str, market_risks: str) -> str | None:
    """Generate an AI-powered risk analysis summary."""
    prompt = (
        f"Provide a risk intelligence briefing for a farmer in {location}.\n\n"
        f"**Composite Risk Score:** {risk_score}/100\n\n"
        f"**Weather alerts:**\n{weather_alerts}\n\n"
        f"**Disease risks:**\n{disease_risks}\n\n"
        f"**Market risks:**\n{market_risks}\n\n"
        "Provide:\n"
        "1. A one-line risk verdict (critical/moderate/low)\n"
        "2. Top 3 priority actions ranked by urgency\n"
        "3. What to monitor in the next 48 hours\n"
        "4. One proactive step to reduce future risk"
    )
    return ai_generate(prompt, AGRO_SYSTEM, max_tokens=600)


@st.cache_data(show_spinner=False, ttl=3600)
def ai_hazard_briefing(location: str, d_prob: float, h_prob: float, f_prob: float,
                       features_summary: str) -> str | None:
    """Generate an AI-powered hazard analysis briefing for the dashboard."""
    prompt = (
        f"Provide a brief hazard intelligence summary for {location}.\n\n"
        f"**ML Model Predictions:**\n"
        f"- Drought probability: {d_prob:.0f}%\n"
        f"- Heatwave probability: {h_prob:.0f}%\n"
        f"- Flood probability: {f_prob:.0f}%\n\n"
        f"**Key environmental data:**\n{features_summary}\n\n"
        "Write 2-3 concise paragraphs interpreting these risks for a farmer. "
        "Highlight the most critical threat and recommend immediate protective actions."
    )
    return ai_generate(prompt, AGRO_SYSTEM, max_tokens=500)


@st.cache_data(show_spinner=False, ttl=3600)
def ai_market_insight(crop: str, price: int, demand: str, trend: str, season_outlook: str) -> str | None:
    """Generate AI-powered market selling strategy for a specific crop."""
    prompt = (
        f"Provide a selling strategy for **{crop}**.\n\n"
        f"- Current price: ₹{price}/quintal\n"
        f"- Demand: {demand}\n"
        f"- Trend: {trend}\n"
        f"- Seasonal outlook: {season_outlook}\n\n"
        "Advise on:\n"
        "1. Should the farmer sell now or hold?\n"
        "2. Expected price movement in next 30 days\n"
        "3. Best channel to sell (mandi, FPO, direct contract, online)\n"
        "4. One tip to maximize returns\n"
        "Keep it under 150 words."
    )
    return ai_generate(prompt, AGRO_SYSTEM, max_tokens=400)


@st.cache_data(show_spinner=False, ttl=3600)
def ai_crop_advice(crop: str, score: int, soil: str, weather_summary: str, reasons: str) -> str | None:
    """Generate AI-powered planting advice for a recommended crop."""
    prompt = (
        f"A farmer is considering planting **{crop}** (match score: {score}%).\n\n"
        f"**Soil:** {soil}\n"
        f"**Current weather:** {weather_summary}\n"
        f"**System analysis:**\n{reasons}\n\n"
        "Provide brief planting advice:\n"
        "1. Is this a good choice right now? (Yes/Maybe/No with reason)\n"
        "2. Key preparation steps before sowing\n"
        "3. Expected challenges and how to mitigate them\n"
        "Keep it under 120 words."
    )
    return ai_generate(prompt, AGRO_SYSTEM, max_tokens=350)
