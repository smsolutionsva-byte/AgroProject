"""Shared UI components — premium CSS, sidebar navigation, and reusable elements."""
import streamlit as st


def inject_global_css():
    """Inject the global premium CSS design system."""
    st.markdown("""
<style>
    /* ═══════════════════════════════════════════════════════════════════════
       AGROSYNC DESIGN SYSTEM — Premium Dark Theme
       ═══════════════════════════════════════════════════════════════════════ */

    /* ── Reset & Base ──────────────────────────────────────────────────── */
    .block-container {
        padding: 2rem 2.5rem 1rem 2.5rem !important;
        max-width: 1400px;
    }
    #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; }
    div[data-testid="stDecoration"] { display: none; }

    /* ── Typography ────────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    h1, h2, h3, h4 { font-weight: 700 !important; letter-spacing: -0.02em; }

    /* ── Sidebar ───────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0f1a 0%, #111827 50%, #0d1117 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    section[data-testid="stSidebar"] .block-container {
        padding: 1.5rem 1rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #94a3b8;
    }

    /* Nav links */
    section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
        background: transparent !important;
        border-radius: 10px !important;
        padding: 0.55rem 0.8rem !important;
        margin: 2px 0 !important;
        transition: all 0.2s ease !important;
        border: 1px solid transparent !important;
    }
    section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
        background: rgba(99, 102, 241, 0.12) !important;
        border-color: rgba(99, 102, 241, 0.2) !important;
    }
    section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"][aria-current="page"] {
        background: linear-gradient(135deg, rgba(99,102,241,0.18) 0%, rgba(139,92,246,0.12) 100%) !important;
        border-color: rgba(99, 102, 241, 0.3) !important;
    }
    section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] p {
        font-size: 0.88rem !important;
        font-weight: 500 !important;
    }

    /* ── Page header ───────────────────────────────────────────────────── */
    .page-header {
        margin-bottom: 1.5rem;
    }
    .page-header h1 {
        font-size: 1.75rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #f8fafc 0%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.15rem !important;
    }
    .page-header .subtitle {
        font-size: 0.9rem;
        color: #64748b;
        margin-top: 0;
    }

    /* ── Glass cards ───────────────────────────────────────────────────── */
    .glass-card {
        background: rgba(17, 24, 39, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 16px;
        padding: 1.3rem 1.5rem;
        margin-bottom: 0.75rem;
        transition: all 0.25s ease;
    }
    .glass-card:hover {
        border-color: rgba(99, 102, 241, 0.25);
        box-shadow: 0 4px 24px rgba(0,0,0,0.3);
    }

    /* ── Metric cards ──────────────────────────────────────────────────── */
    .metric-card {
        background: rgba(17, 24, 39, 0.5);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        text-align: center;
    }
    .metric-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #64748b;
        margin-bottom: 0.35rem;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1.1;
    }
    .metric-sub {
        font-size: 0.75rem;
        color: #475569;
        margin-top: 0.25rem;
    }

    /* ── Risk / status bars ────────────────────────────────────────────── */
    .risk-bar {
        background: rgba(17, 24, 39, 0.6);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 1rem 1.3rem;
        margin-bottom: 0.6rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        transition: all 0.2s ease;
    }
    .risk-bar:hover { border-color: rgba(255,255,255,0.12); }
    .risk-bar .rb-left { display: flex; align-items: center; gap: 0.8rem; }
    .risk-bar .rb-icon { font-size: 1.5rem; }
    .risk-bar .rb-name { font-weight: 600; font-size: 1rem; }
    .risk-bar .rb-sub  { font-size: 0.78rem; color: #64748b; }

    .rb-badge {
        font-size: 0.78rem;
        font-weight: 600;
        padding: 5px 14px;
        border-radius: 20px;
        letter-spacing: 0.3px;
    }
    .rb-badge.low    { background: rgba(34,197,94,0.15); color: #4ade80; }
    .rb-badge.medium { background: rgba(245,158,11,0.15); color: #fbbf24; }
    .rb-badge.high   { background: rgba(239,68,68,0.15); color: #f87171; }

    /* ── Buttons ───────────────────────────────────────────────────────── */
    .stButton > button[kind="primary"],
    button[data-testid="stFormSubmitButton"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 2px 12px rgba(99,102,241,0.25) !important;
    }
    .stButton > button[kind="primary"]:hover,
    button[data-testid="stFormSubmitButton"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 20px rgba(99,102,241,0.4) !important;
    }

    .stButton > button:not([kind="primary"]) {
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        background: rgba(255,255,255,0.04) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:not([kind="primary"]):hover {
        background: rgba(255,255,255,0.08) !important;
        border-color: rgba(255,255,255,0.18) !important;
    }

    /* ── Inputs ─────────────────────────────────────────────────────────── */
    .stTextInput > div > div > input,
    .stSelectbox > div > div {
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        background: rgba(15, 23, 42, 0.6) !important;
        transition: border-color 0.2s ease !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: rgba(99, 102, 241, 0.5) !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15) !important;
    }

    /* ── Expanders ──────────────────────────────────────────────────────── */
    .streamlit-expanderHeader {
        border-radius: 12px !important;
        background: rgba(17, 24, 39, 0.4) !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }
    details[data-testid="stExpander"] {
        border: 1px solid rgba(255,255,255,0.06) !important;
        border-radius: 14px !important;
        background: rgba(17, 24, 39, 0.3) !important;
    }

    /* ── Metrics (Streamlit built-in) ───────────────────────────────────── */
    div[data-testid="stMetric"] {
        background: rgba(17, 24, 39, 0.5);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 1rem 1.2rem;
    }
    div[data-testid="stMetric"] label {
        color: #64748b !important;
        font-weight: 600 !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        font-weight: 800 !important;
    }

    /* ── Dataframes ────────────────────────────────────────────────────── */
    .stDataFrame {
        border-radius: 14px !important;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.06) !important;
    }

    /* ── Alerts ─────────────────────────────────────────────────────────── */
    .stAlert {
        border-radius: 12px !important;
        border: none !important;
    }
    div[data-testid="stAlert"] {
        border-radius: 12px !important;
    }

    /* ── Chat ──────────────────────────────────────────────────────────── */
    .stChatMessage {
        border-radius: 14px !important;
        border: 1px solid rgba(255,255,255,0.05) !important;
        background: rgba(17, 24, 39, 0.4) !important;
    }

    /* ── Scrollbar ─────────────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }

    /* ── Status colors ─────────────────────────────────────────────────── */
    .clr-green  { color: #4ade80; }
    .clr-yellow { color: #fbbf24; }
    .clr-red    { color: #f87171; }
    .clr-blue   { color: #60a5fa; }
    .clr-purple { color: #a78bfa; }
    .clr-muted  { color: #64748b; }

    /* ── Dividers ──────────────────────────────────────────────────────── */
    hr { border-color: rgba(255,255,255,0.06) !important; margin: 1.5rem 0 !important; }

    /* ── Download button ───────────────────────────────────────────────── */
    .stDownloadButton > button {
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
    }

    /* ── Tab styling ───────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        padding: 0.5rem 1.2rem !important;
        font-weight: 500 !important;
    }

    /* ── Responsive ────────────────────────────────────────────────────── */
    @media (max-width: 768px) {
        .block-container { padding: 1rem 1rem !important; }
        .metric-value { font-size: 1.5rem; }
    }
</style>
""", unsafe_allow_html=True)


def render_sidebar(active_page: str = ""):
    """Render the premium sidebar with branding and navigation."""
    with st.sidebar:
        try:
            # Logo / brand
            st.markdown("""
            <div style="padding: 0.5rem 0 1rem 0;">
                <div style="font-size: 1.4rem; font-weight: 800; letter-spacing: -0.03em;">
                    <span style="background: linear-gradient(135deg, #6366f1, #a78bfa);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    AgroSync</span> <span style="color: #475569; font-weight: 500;">AI</span>
                </div>
                <div style="font-size: 0.72rem; color: #475569; margin-top: 2px; letter-spacing: 0.5px;">
                    INTELLIGENT FARM PLATFORM
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.divider()
            
            # Navigation section
            st.markdown("""<p style="font-size: 0.7rem; color: #64748b; text-transform: uppercase;
                        letter-spacing: 0.5px; font-weight: 600; margin: 0.5rem 0;">Navigation</p>""", unsafe_allow_html=True)

            # Create columns for better layout control
            col1, col2 = st.columns([0.95, 0.05])
            with col1:
                # Navigation links
                st.page_link("dashboard.py", label="📊 Dashboard")
                st.page_link("pages/1_Relief_Brain.py", label="🚑 Relief Brain")
                st.page_link("pages/2_Tactical_Engine.py", label="🧠 Tactical AI")
                st.page_link("pages/3_Market_Analysis.py", label="📈 Market Insights")
                st.page_link("pages/4_Crop_Recommendation.py", label="🌱 Crop Advisor")
                st.page_link("pages/5_Weather_Intelligence.py", label="🌦️ Weather Intel")
                st.page_link("pages/6_Risk_Alerts.py", label="🚨 Risk Alerts")

            st.divider()

            # Location context
            loc = st.session_state.get("location_name", "Bengaluru")
            lat = st.session_state.get("lat", 12.97)
            lon = st.session_state.get("lon", 77.59)
            
            st.markdown("""<p style="font-size: 0.7rem; color: #64748b; text-transform: uppercase;
                        letter-spacing: 0.5px; font-weight: 600; margin: 0.5rem 0;">Location</p>""", unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.03); border-radius: 10px;
                        padding: 0.8rem; border: 1px solid rgba(255,255,255,0.05);">
                <div style="font-size: 0.88rem; font-weight: 600; color: #e2e8f0;">
                    📍 {loc}</div>
                <div style="font-size: 0.72rem; color: #475569; margin-top: 2px;">
                    {lat:.4f}, {lon:.4f}</div>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.sidebar.error(f"⚠️ Sidebar error: {str(e)}")


def page_header(title: str, subtitle: str):
    """Render a consistent page header."""
    st.markdown(f"""
    <div class="page-header">
        <h1>{title}</h1>
        <p class="subtitle">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)
