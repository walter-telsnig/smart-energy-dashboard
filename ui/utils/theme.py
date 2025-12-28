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

          /* Page background */
          .stApp { background: #f6f8fb; }

          .block-container {
            padding-top: 1.5rem;
            max-width: 1250px;
          }

          /* Sidebar background */
          section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0b2d4a 0%, #0a2440 100%);
          }

          /* Sidebar header text (keep white) */
          section[data-testid="stSidebar"] h1,
          section[data-testid="stSidebar"] h2,
          section[data-testid="stSidebar"] h3,
          section[data-testid="stSidebar"] .stCaptionContainer,
          section[data-testid="stSidebar"] .stMarkdown {
            color: #ffffff !important;
          }

          /* =========================
             NAV BUTTONS
             ========================= */

          /* Style the actual Streamlit button */
          section[data-testid="stSidebar"] .nav-btn div.stButton > button {
            width: 100% !important;
            border-radius: 14px !important;
            padding: 14px 16px !important;
            border: 1px solid rgba(255,255,255,0.15) !important;
            background: rgba(255,255,255,0.92) !important;
            text-align: left !important;
          }
          section[data-testid="stSidebar"] .nav-btn div.stButton > button p,
          section[data-testid="stSidebar"] .nav-btn div.stButton > button span {
            color: #0f172a !important;   
            opacity: 1 !important;      
            font-weight: 800 !important;
            margin: 0 !important;
          }

          /* Hover */
          section[data-testid="stSidebar"] .nav-btn div.stButton > button:hover {
            background: #f1f5f9 !important;
          }

          /* ACTIVE button wrapper -> red button */
          section[data-testid="stSidebar"] .nav-btn.active div.stButton > button {
            background: #ff4d4f !important;
            border: 1px solid rgba(255,255,255,0.25) !important;
          }

          /* ACTIVE text -> white */
          section[data-testid="stSidebar"] .nav-btn.active div.stButton > button p,
          section[data-testid="stSidebar"] .nav-btn.active div.stButton > button span {
            color: #ffffff !important;
            opacity: 1 !important;
          }

          /* =========================
             KPI cards (optional)
             ========================= */
          .kpi-card {
            background: #ffffff !important;
            border: 1px solid rgba(0,0,0,0.06) !important;
            border-radius: 16px !important;
            padding: 18px 18px !important;
            box-shadow: 0 10px 22px rgba(18, 38, 63, 0.06) !important;
          }
          .kpi-card.kpi-pv { background: #FFF4DA !important; }
          .kpi-card.kpi-consumption { background: #EAF4FF !important; }
          .kpi-card.kpi-price { background: #F2EFFF !important; }
          .kpi-card.kpi-self { background: #EAFBEF !important; }

          .kpi-title { font-size: 0.9rem; opacity: 0.7; margin-bottom: 6px; }
          .kpi-value { font-size: 1.7rem; font-weight: 800; }
          .kpi-sub { font-size: 0.9rem; opacity: 0.65; margin-top: 6px; }

          /* Inputs */
          .stTextInput input, .stNumberInput input { border-radius: 12px !important; }
          .stButton button { border-radius: 12px !important; font-weight: 700 !important; }

        </style>
        """,
        unsafe_allow_html=True,
    )


def sidebar_nav(active: str = "Dashboard") -> None:
    """
    Styled sidebar nav. Pass active="PV"/"Prices"/etc. to highlight current page.
    """
    with st.sidebar:
        st.markdown("## Smart Energy Dashboard")
        st.caption("Track, analyze, optimize your energy.")
        st.markdown("---")

        def nav_button(label: str, target: str | None, key: str):
            wrapper_class = "nav-btn active" if label == active else "nav-btn"

            st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)
            clicked = st.button(label, use_container_width=True, key=key)
            st.markdown("</div>", unsafe_allow_html=True)

            if clicked:
                if target is None:
                    st.rerun()
                else:
                    st.switch_page(target)

        # NOTE: active must match the label string exactly
        nav_button("🏠  Dashboard", None, key="nav_dashboard")
        nav_button("☀️  PV", "pages/01_PV.py", key="nav_pv")
        nav_button("💶  Prices", "pages/02_Prices.py", key="nav_prices")
        nav_button("🏠  Consumption", "pages/03_Consumption.py", key="nav_consumption")
        nav_button("📊  Compare", "pages/04_Compare.py", key="nav_compare")
        nav_button("✅  Recommendations", "pages/06_Recommendations.py", key="nav_reco")
        nav_button("🔋  Battery Sim", "pages/99_Battery_Sim.py", key="nav_battery")

        # st.markdown("---")
        # if st.button("Logout", use_container_width=True, key="nav_logout"):
        #     st.session_state["token"] = None
        #     st.switch_page("pages/00_Login.py")
