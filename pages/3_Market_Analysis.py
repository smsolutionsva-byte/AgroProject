import streamlit as st
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv
from utils.ui import inject_global_css, render_sidebar, page_header
from utils.gemini import ai_market_insight

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Market Analysis — AgroSync", page_icon="📈", layout="wide")
inject_global_css()


# ── Crop market data (rule-based, no external API needed) ────────────────────
def get_market_data():
    """Seasonal crop price data with trends and demand signals."""
    month = datetime.now().month

    # Base prices (INR/quintal) with seasonal multipliers
    crops = {
        "Rice": {
            "base_price": 2200,
            "seasonal": {(1, 3): 1.1, (4, 6): 0.95, (7, 9): 0.9, (10, 12): 1.15},
            "demand": "High" if month in [10, 11, 12, 1] else "Medium",
            "trend": "up" if month in [10, 11, 12] else "stable",
            "tip": "Post-harvest prices rise from Oct-Jan. Store safely if possible.",
        },
        "Wheat": {
            "base_price": 2275,
            "seasonal": {(1, 3): 0.95, (4, 6): 1.1, (7, 9): 1.05, (10, 12): 0.98},
            "demand": "High" if month in [4, 5, 6] else "Medium",
            "trend": "up" if month in [3, 4, 5] else "stable",
            "tip": "Best selling window is Apr-Jun when stocks are low.",
        },
        "Millet (Ragi/Bajra)": {
            "base_price": 2500,
            "seasonal": {(1, 3): 1.05, (4, 6): 1.0, (7, 9): 0.95, (10, 12): 1.1},
            "demand": "Rising" if month in [1, 2, 3, 10, 11, 12] else "Medium",
            "trend": "up",
            "tip": "Millets are gaining popularity due to health trends. Premium prices in urban markets.",
        },
        "Tomato": {
            "base_price": 1500,
            "seasonal": {(1, 3): 1.2, (4, 6): 0.8, (7, 9): 1.5, (10, 12): 0.9},
            "demand": "High" if month in [7, 8, 9] else "Medium",
            "trend": "volatile",
            "tip": "Tomato prices swing heavily. Sell quickly during shortage months (Jul-Sep).",
        },
        "Cotton": {
            "base_price": 6620,
            "seasonal": {(1, 3): 1.0, (4, 6): 0.95, (7, 9): 0.9, (10, 12): 1.1},
            "demand": "High" if month in [10, 11, 12] else "Medium",
            "trend": "up" if month in [10, 11] else "stable",
            "tip": "Best prices during ginning season (Oct-Dec). Avoid selling at harvest floor.",
        },
        "Sugarcane": {
            "base_price": 315,
            "seasonal": {(1, 3): 1.0, (4, 6): 1.0, (7, 9): 1.0, (10, 12): 1.05},
            "demand": "Steady",
            "trend": "stable",
            "tip": "FRP is government-regulated. Focus on yield per acre for better returns.",
        },
        "Soybean": {
            "base_price": 4600,
            "seasonal": {(1, 3): 1.05, (4, 6): 1.1, (7, 9): 0.9, (10, 12): 1.0},
            "demand": "High" if month in [4, 5, 6] else "Medium",
            "trend": "up" if month in [3, 4, 5] else "stable",
            "tip": "Soybean meal demand drives prices. Export season (Mar-Jun) brings best returns.",
        },
        "Onion": {
            "base_price": 1200,
            "seasonal": {(1, 3): 0.9, (4, 6): 1.3, (7, 9): 1.5, (10, 12): 1.1},
            "demand": "High" if month in [5, 6, 7, 8] else "Medium",
            "trend": "volatile",
            "tip": "Prices spike during monsoon when supply drops. Store in well-ventilated spaces.",
        },
    }

    results = []
    for crop, info in crops.items():
        multiplier = 1.0
        for (start, end), mult in info["seasonal"].items():
            if start <= month <= end:
                multiplier = mult
                break
        current_price = int(info["base_price"] * multiplier)

        results.append({
            "crop": crop,
            "price": current_price,
            "demand": info["demand"],
            "trend": info["trend"],
            "tip": info["tip"],
        })

    return results


def get_demand_forecast():
    """Quarterly demand outlook based on season."""
    month = datetime.now().month
    if month in [1, 2, 3]:
        return "Q1 (Jan-Mar)", "Rabi harvest season. Wheat, mustard, and chickpea supply peaks. Focus on storage versus immediate sale."
    elif month in [4, 5, 6]:
        return "Q2 (Apr-Jun)", "Pre-monsoon period. Vegetable prices rise due to heat. Good window for selling stored grains."
    elif month in [7, 8, 9]:
        return "Q3 (Jul-Sep)", "Monsoon season. Fresh produce prices spike due to transport disruptions. Perishable crops sell at premium."
    else:
        return "Q4 (Oct-Dec)", "Kharif harvest. Rice, cotton, soybean supply increases. Early sellers get better prices before glut."


# ── Main UI ──────────────────────────────────────────────────────────────────
def main():
    render_sidebar("Market Insights")

    page_header("Market Insights", "Crop price trends, demand forecasts, and selling strategies.")

    # Demand outlook
    quarter, outlook = get_demand_forecast()
    st.markdown(f"""
    <div class="glass-card" style="border-left: 3px solid #6366f1;">
        <span style="font-weight: 600;">{quarter} Outlook:</span> {outlook}
    </div>
    """, unsafe_allow_html=True)

    # Market data
    market = get_market_data()
    st.markdown("""
    <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.5px; color: #64748b; margin: 1rem 0 0.5rem;">
        Current Price Estimates</div>
    """, unsafe_allow_html=True)
    st.caption("Prices are indicative based on seasonal patterns (INR/quintal).")

    # Price cards — 4 per row
    for i in range(0, len(market), 4):
        cols = st.columns(4)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(market):
                break
            item = market[idx]
            trend_color = {"up": "#4ade80", "stable": "#fbbf24", "down": "#f87171", "volatile": "#f87171"}
            trend_arrow = {"up": "↑", "stable": "→", "down": "↓", "volatile": "↕"}

            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{item['crop']}</div>
                    <div class="metric-value" style="font-size: 1.5rem;">₹{item['price']:,}</div>
                    <div class="metric-sub" style="color: {trend_color.get(item['trend'], '#fbbf24')};">
                        {trend_arrow.get(item['trend'], '→')} {item['trend'].title()} · {item['demand']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Detailed analysis
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.5px; color: #64748b; margin-bottom: 0.5rem;">
        Crop-wise Insights</div>
    """, unsafe_allow_html=True)

    selected_crop = st.selectbox("Select crop for details", [m["crop"] for m in market])
    item = next(m for m in market if m["crop"] == selected_crop)

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Current Price", f"₹{item['price']:,}/q")
    mc2.metric("Demand", item["demand"])
    mc3.metric("Trend", item["trend"].title())

    st.markdown(f"**Selling Strategy:** {item['tip']}")

    # AI Market Insight
    quarter, outlook = get_demand_forecast()
    with st.spinner("AI analyzing market…"):
        ai_insight = ai_market_insight(
            selected_crop, item["price"], item["demand"], item["trend"], outlook
        )
    if ai_insight:
        st.markdown(f"""
        <div class="glass-card" style="border-left: 3px solid #6366f1; margin-top: 0.5rem;">
            <span style="background:#6366f1;color:#fff;font-size:0.65rem;padding:2px 8px;border-radius:999px;">AI Insight</span>
            <div style="margin-top: 0.5rem;">{ai_insight}</div>
        </div>
        """, unsafe_allow_html=True)

    # Best crops to sell now
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                letter-spacing: 0.5px; color: #64748b; margin-bottom: 0.5rem;">
        Best Crops to Sell Right Now</div>
    """, unsafe_allow_html=True)
    high_demand = [m for m in market if m["demand"] in ["High", "Rising"]]
    if high_demand:
        for m in high_demand:
            st.success(f"**{m['crop']}** — Demand: {m['demand']} | ₹{m['price']:,}/q | {m['tip']}")
    else:
        st.info("No crops are in peak demand right now. Consider storage until the next seasonal window.")


if __name__ == "__main__":
    main()
