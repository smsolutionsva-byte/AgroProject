import streamlit as st
import pandas as pd
from duckduckgo_search import DDGS
import os
from datetime import datetime
from dotenv import load_dotenv
from utils.ui import inject_global_css, render_sidebar, page_header
from utils.gemini import ai_relief_plan

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# ── Config ───────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Relief Brain — AgroSync", page_icon="🚑", layout="wide")
inject_global_css()
BRAIN_FILE = "disaster_brain.pkl"


# ── Brain persistence (knowledge cache) ──────────────────────────────────────
def load_brain():
    if os.path.exists(BRAIN_FILE):
        try:
            df = pd.read_pickle(BRAIN_FILE)
            if "application_guide" not in df.columns:
                df["application_guide"] = "Guide not generated for older entries."
            return df
        except Exception:
            pass
    return pd.DataFrame(columns=[
        "location", "disaster_type", "scheme_name",
        "description", "source_link", "date_added", "application_guide",
    ])


def save_brain(df):
    df.to_pickle(BRAIN_FILE)


# ── Regional knowledge base ─────────────────────────────────────────────────
REGION_DATA = {
    "india": {
        "keywords": ["india", "karnataka", "bengaluru", "maharashtra", "punjab",
                      "up", "bihar", "tamil nadu", "kerala", "gujarat"],
        "where": (
            "- **Village Level:** Contact your Panchayat Secretary or Village Accountant (Patwari/Talathi).\n"
            "- **Online:** Visit your nearest Common Service Centre (CSC) and apply on the PMFBY or state agriculture portal.\n"
        ),
        "doc_id": "Aadhaar Card, PAN, or Voter ID.",
        "doc_land": "Recent land records (RTC/Pahani/7/12 extract) or tenancy agreements.",
        "url": "https://pmfby.gov.in/",
    },
    "madagascar": {
        "keywords": ["madagascar", "antananarivo", "toamasina", "fianarantsoa"],
        "where": (
            "- **Village Level:** Report crop damage to your local Fokontany chief.\n"
            "- **National:** Contact BNGRC or local Ministry of Agriculture offices.\n"
        ),
        "doc_id": "National Malagasy Identity Card (CIN).",
        "doc_land": "Proof of land ownership verified by the Fokontany.",
        "url": "https://bngrc.mid.gov.mg/",
    },
    "philippines": {
        "keywords": ["philippines", "manila", "mindanao", "visayas", "luzon"],
        "where": (
            "- **Municipal Level:** Report to your Municipal Agriculture Office (MAO).\n"
            "- **Funding:** Apply for the SURE Assistance Program.\n"
        ),
        "doc_id": "Valid Government ID and RSBSA enrollment.",
        "doc_land": "Barangay certification or proof of cultivation.",
        "url": "https://www.da.gov.ph/",
    },
    "australia": {
        "keywords": ["australia", "nsw", "queensland", "victoria", "south australia", "western australia"],
        "where": "- **State Specific:** Use QRIDA (Qld) or RAA (NSW) for Special Disaster Grants.\n",
        "doc_id": "Driver's License or Passport.",
        "doc_land": "Property titles, tax records, and ABN.",
        "url": "https://www.servicesaustralia.gov.au/farm-household-allowance",
    },
    "kenya": {
        "keywords": ["kenya", "nairobi", "mombasa", "turkana", "baringo", "asal"],
        "where": (
            "- **County Level:** Report to the County Department of Agriculture.\n"
            "- **National:** Contact NDMA (National Drought Management Authority).\n"
        ),
        "doc_id": "Kenyan National ID Card.",
        "doc_land": "Land title deeds or community trust land verification.",
        "url": "https://www.ndma.go.ke/",
    },
    "usa": {
        "keywords": ["us", "usa", "texas", "california", "florida", "iowa"],
        "where": (
            "- **Local Office:** Visit your county USDA Farm Service Agency (FSA) office.\n"
            "- **Online:** Register at DisasterAssistance.gov.\n"
        ),
        "doc_id": "State ID, Driver's License, or SSN.",
        "doc_land": "Property deeds, FSA farm numbers, crop insurance policies.",
        "url": "https://www.disasterassistance.gov/",
    },
}

DISASTER_TIPS = {
    "drought": "Ask your local agricultural office about free drought-resistant seed programs.",
    "flood": "Record damage to equipment and soil erosion — some funds cover infrastructure.",
    "heatwave": "Ask about subsidies for drip irrigation or shade nets.",
}


def _match_region(location: str):
    loc = location.lower()
    for region_data in REGION_DATA.values():
        if any(kw in loc for kw in region_data["keywords"]):
            return region_data
    return None


def build_farmer_guide(location: str, disaster_type: str) -> tuple[str, str]:
    """Build a localized action guide and return (guide_text, official_url)."""
    region = _match_region(location)

    if region:
        where = region["where"]
        doc_id = region["doc_id"]
        doc_land = region["doc_land"]
        official_url = region["url"]
    else:
        where = "- **Local Govt:** Visit your nearest municipal or regional agriculture department.\n"
        doc_id = "Valid Government Issued ID."
        doc_land = "Property deeds, leases, or official tax records."
        official_url = ""

    guide = f"**Relief Protocol for {location.title()} — {disaster_type.title()}**\n\n"
    guide += "**Where to Apply:**\n" + where + "\n"
    guide += "**Documents Required:**\n"
    guide += f"- Identification: {doc_id}\n"
    guide += f"- Land Proof: {doc_land}\n"
    guide += "- Bank Details: Active bank account passbook for direct transfers.\n"
    guide += "- Evidence: Photos/videos of damaged crops (do not clear the field before inspection).\n\n"

    tip = DISASTER_TIPS.get(disaster_type.lower(), "")
    if tip:
        guide += f"**Pro Tip:** {tip}\n"

    return guide, official_url


# ── Web search with caching ─────────────────────────────────────────────────
@st.cache_data(show_spinner=False, ttl=3600)
def fetch_schemes(location: str, disaster_type: str):
    guide, official_url = build_farmer_guide(location, disaster_type)
    results = []

    if official_url:
        results.append({
            "location": location.lower(),
            "disaster_type": disaster_type.lower(),
            "scheme_name": f"Official {location.title()} Relief Portal",
            "description": f"Verified government contact point for {disaster_type.lower()} disaster relief.",
            "source_link": official_url,
            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "application_guide": guide,
        })

    try:
        query = f"{location} {disaster_type} disaster relief OR agricultural assistance OR government fund"
        ddgs = DDGS()
        for item in ddgs.text(query, max_results=5):
            results.append({
                "location": location.lower(),
                "disaster_type": disaster_type.lower(),
                "scheme_name": item.get("title", "Untitled"),
                "description": item.get("body", ""),
                "source_link": item.get("href", ""),
                "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "application_guide": guide,
            })
    except Exception as e:
        st.error(f"Search error: {e}")

    return results


# ── Main UI ──────────────────────────────────────────────────────────────────
def main():
    # Sidebar navigation
    render_sidebar("Relief Brain")

    # Header
    page_header("Disaster Relief Brain", "Find relief schemes and get step-by-step application guides for your region.")

    brain_df = load_brain()

    # Defaults (support teleport from dashboard)
    if "search_loc_input" not in st.session_state:
        st.session_state["search_loc_input"] = "Bengaluru"
    if "search_dis_input" not in st.session_state:
        st.session_state["search_dis_input"] = "Flood"

    # Handle teleport from dashboard
    if "teleport_loc" in st.session_state:
        st.session_state["search_loc_input"] = st.session_state["teleport_loc"]
        incoming = st.session_state.get("teleport_dis", "Flood").lower()
        if "drought" in incoming:
            st.session_state["search_dis_input"] = "Drought"
        elif "heatwave" in incoming:
            st.session_state["search_dis_input"] = "Heatwave"
        else:
            st.session_state["search_dis_input"] = "Flood"
        loc_name = st.session_state["teleport_loc"]
        del st.session_state["teleport_loc"]
        del st.session_state["teleport_dis"]
        st.success(f"Imported hazard context for **{loc_name}**")

    # Search form
    with st.form("search_form"):
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            location_input = st.text_input("Location", key="search_loc_input", placeholder="e.g. Maharashtra, Texas, Kenya")
        with c2:
            disaster_input = st.selectbox("Disaster Type", ["Flood", "Drought", "Heatwave"], key="search_dis_input")
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Search", type="primary", use_container_width=True)

    if submitted:
        if not location_input.strip():
            st.warning("Please enter a valid location.")
            return

        location_norm = location_input.strip().lower()
        disaster_norm = disaster_input.lower()

        brain_df["date_added"] = pd.to_datetime(brain_df["date_added"], errors="coerce")
        cached = brain_df[
            (brain_df["location"] == location_norm) & (brain_df["disaster_type"] == disaster_norm)
        ]

        data_fresh = False
        if not cached.empty:
            latest = cached["date_added"].max()
            if pd.notna(latest) and (datetime.now() - latest).days < 7:
                data_fresh = True

        if data_fresh:
            display_data = cached.copy()
            display_data["date_added"] = display_data["date_added"].dt.strftime("%Y-%m-%d")
            display_data = display_data.to_dict("records")
        else:
            if not cached.empty:
                brain_df = brain_df[
                    ~((brain_df["location"] == location_norm) & (brain_df["disaster_type"] == disaster_norm))
                ]
            with st.spinner("Fetching relief schemes and building action plan…"):
                new_data = fetch_schemes(location_norm, disaster_norm)

            if new_data:
                display_data = new_data
                new_df = pd.DataFrame(new_data)
                new_df["date_added"] = pd.to_datetime(new_df["date_added"])
                updated = pd.concat([brain_df, new_df], ignore_index=True).drop_duplicates(subset=["source_link"])
                save_brain(updated)
            else:
                st.warning("No results found. Try adjusting your search.")
                display_data = []

        if display_data:
            st.markdown("---")

            # AI-generated action plan
            guide_text = display_data[0].get("application_guide", "")
            region_info = guide_text  # pass template guide as context for AI
            with st.spinner("AI generating personalized action plan…"):
                ai_plan = ai_relief_plan(location_norm, disaster_norm, region_info)

            plan_text = ai_plan if ai_plan else guide_text

            if plan_text:
                st.markdown("""
                <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                            letter-spacing: 0.5px; color: #64748b; margin-bottom: 0.5rem;">
                    Your Action Plan</div>
                """, unsafe_allow_html=True)
                badge = ' <span style="background:#6366f1;color:#fff;font-size:0.65rem;padding:2px 8px;border-radius:999px;margin-left:8px;">AI Generated</span>' if ai_plan else ''
                st.markdown(f'<div class="glass-card">{plan_text}{badge}</div>', unsafe_allow_html=True)

            # Download
            download_text = f"FARMER ACTION PLAN: {location_input.upper()} ({disaster_input.upper()})\n"
            download_text += "=" * 50 + "\n\n"
            download_text += plan_text.replace("**", "") + "\n\n"
            download_text += "LINKS & RESOURCES:\n" + "-" * 50 + "\n"
            for item in display_data:
                download_text += f"• {item['scheme_name']}\n  {item['source_link']}\n\n"

            st.download_button(
                "Download Action Plan (.txt)",
                data=download_text,
                file_name=f"{location_input.replace(' ', '_')}_{disaster_input}_plan.txt",
                mime="text/plain",
            )

            # Scheme cards
            st.markdown("""
            <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase;
                        letter-spacing: 0.5px; color: #64748b; margin: 1rem 0 0.5rem;">
                Relief Schemes & Resources</div>
            """, unsafe_allow_html=True)
            for idx, item in enumerate(display_data):
                with st.expander(f"{idx + 1}. {item['scheme_name']}", expanded=(idx == 0)):
                    st.markdown(item["description"])
                    st.markdown(f"[Visit resource →]({item['source_link']})")
                    date_str = item["date_added"][:10] if isinstance(item["date_added"], str) else item["date_added"].strftime("%Y-%m-%d")
                    st.caption(f"{item['location'].title()}  •  Fetched {date_str}")


if __name__ == "__main__":
    main()