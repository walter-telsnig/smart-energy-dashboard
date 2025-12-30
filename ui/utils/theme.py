"""
shared UI theme and navigation for the Smart Energy Dashboard
+ Consistent look across all pages
"""
from __future__ import annotations
import streamlit as st


def apply_global_style() -> None:
    st.markdown(
        """
        <style>
          /* Hide Streamlit default multipage nav */
          [data-testid="stSidebarNav"] { display: none !important; }
          [data-testid="stSidebarNavItems"] { display: none !important; }

          /* App background + layout */
          .stApp { background: #f6f8fb; }
          .block-container { padding-top: 1.5rem; max-width: 1250px; }

          /* Sidebar background */
          section[data-testid="stSidebar"]{
            background: linear-gradient(180deg, #0b2d4a 0%, #0a2440 100%) !important;
            border-right: 1px solid rgba(255,255,255,0.08);
          }

          /* Make ALL sidebar text readable (fix “REPORTING/SETTINGS not visible”) */
          section[data-testid="stSidebar"] * { color: #eaf2ff !important; }

          /* Sidebar spacing */
          section[data-testid="stSidebar"] .block-container{
            padding-top: 1.2rem;
            padding-bottom: 1.2rem;
          }

          /* Sidebar header text */
          .sb-title {
            font-size: 1.05rem;
            font-weight: 800;
            letter-spacing: 0.02em;
            margin-bottom: 0.2rem;
          }
          .sb-subtitle {
            font-size: 0.85rem;
            opacity: 0.80;
            margin-bottom: 0.9rem;
          }
          .sb-group {
            margin-top: 0.9rem;
            margin-bottom: 0.45rem;
            font-size: 0.78rem;
            letter-spacing: 0.14em;
            opacity: 0.95;
            font-weight: 800;
            text-transform: uppercase;
          }

          /* Sidebar buttons (dark style like your Dashboard) */
          section[data-testid="stSidebar"] .stButton>button{
            width: 100%;
            border-radius: 12px !important;
            border: 1px solid rgba(255,255,255,0.10) !important;
            background: rgba(255,255,255,0.06) !important;
            padding: 0.70rem 0.85rem !important;
            text-align: left !important;
            font-weight: 650 !important;
          }
          section[data-testid="stSidebar"] .stButton>button:hover{
            background: rgba(255,255,255,0.12) !important;
            border-color: rgba(255,255,255,0.18) !important;
          }

          /* KPI cards */
          .kpi-card{
            background: #ffffff !important;
            border: 1px solid rgba(0,0,0,0.06) !important;
            border-radius: 16px !important;
            padding: 18px 18px !important;
            box-shadow: 0 10px 22px rgba(18,38,63,0.06) !important;
          }
          .kpi-card.kpi-pv { background: #FFF4DA !important; }
          .kpi-card.kpi-consumption { background: #EAF4FF !important; }
          .kpi-card.kpi-price { background: #F2EFFF !important; }
          .kpi-card.kpi-self { background: #EAFBEF !important; }

          .kpi-title { font-size: 0.9rem; opacity: 0.7; margin-bottom: 6px; }
          .kpi-value { font-size: 1.7rem; font-weight: 800; }
          .kpi-sub { font-size: 0.9rem; opacity: 0.65; margin-top: 6px; }
        </style>
        """,
        unsafe_allow_html=True,
    )
def sidebar_nav(active: str = "Dashboard") -> None:
    from utils.settings import load_settings  # local import = minimal side effects

    # Initialize default view_mode once per session (do not override user changes)
    if "view_mode" not in st.session_state:
        st.session_state["view_mode"] = load_settings().get("default_view_mode", "Hourly View")

    with st.sidebar:
        st.markdown('<div class="sb-title">Smart Energy Dashboard</div>', unsafe_allow_html=True)
        st.markdown('<div class="sb-subtitle">Track, analyze, optimize your energy.</div>', unsafe_allow_html=True)

        def nav_btn(label: str, target: str | None, key: str):
            if label == active:
                clicked = st.button(label, use_container_width=True, key=key, type="primary")
            else:
                clicked = st.button(label, use_container_width=True, key=key)

            if clicked:
                if target is None:
                    st.rerun()
                else:
                    st.switch_page(target)

        nav_btn("🏠  Dashboard", "app.py", "nav_dashboard")
        nav_btn("☀️  PV", "pages/01_PV.py", "nav_pv")
        nav_btn("💶  Prices", "pages/02_Prices.py", "nav_prices")
        nav_btn("🏠  Consumption", "pages/03_Consumption.py", "nav_consumption")
        nav_btn("📊  Compare", "pages/04_Compare.py", "nav_compare")
        nav_btn("✅  Recommendations", "pages/06_Recommendations.py", "nav_reco")
        nav_btn("🔋  Battery Sim", "pages/99_Battery_Sim.py", "nav_battery")

        # NEW: Settings page (minimal)
        nav_btn("⚙️  Settings", "pages/07_Settings.py", "nav_settings")

        st.markdown('<div class="sb-group">Reporting</div>', unsafe_allow_html=True)

        st.session_state["view_mode"] = st.radio(
            "Data Range",
            ["Daily View", "Hourly View"],
            index=1 if st.session_state.get("view_mode") != "Daily View" else 0,
            label_visibility="collapsed",
        )

        st.divider()
        if st.button("Sign out", use_container_width=True, key="nav_signout"):
            st.session_state["token"] = None
            st.switch_page("pages/00_Login.py")
