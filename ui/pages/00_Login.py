# ui/pages/00_Login.py
from __future__ import annotations

import time
import requests
import streamlit as st

API_DEFAULT = "http://localhost:8000"

# ---------------------------
# Helpers
# ---------------------------
def _hide_sidebar_for_landing() -> None:
    st.markdown(
        """
        <style>
          /* Hide sidebar completely */
          section[data-testid="stSidebar"] {
            display: none !important;
          }

          /* Hide top header buttons */
          button[kind="header"] {
            display: none !important;
          }

          /* Page background (MATCH DASHBOARD) */
          .stApp {
            background: #e2edf6;
          }

          /* Centered content width */
          .block-container {
            padding-top: 2.5rem;
            max-width: 1200px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )



def _api_base() -> str:
    return str(st.session_state.get("api_base", API_DEFAULT)).rstrip("/")


def api_login(email: str, password: str) -> tuple[bool, str, str]:
    base = _api_base()
    url = f"{base}/api/v1/token"
    try:
        r = requests.post(url, data={"username": email, "password": password}, timeout=10)
        if r.status_code != 200:
            return False, f"Login failed ({r.status_code}): {r.text}", ""
        token = r.json().get("access_token")
        if not token:
            return False, "Login succeeded but access_token missing.", ""
        return True, "Logged in.", token
    except Exception as e:
        return False, f"Could not reach API: {e}", ""


def api_register(email: str, password: str, full_name: str) -> tuple[bool, str]:
    base = _api_base()
    url = f"{base}/api/v1/accounts/"
    try:
        payload = {"email": email, "password": password, "full_name": full_name}
        r = requests.post(url, json=payload, timeout=10)

        if r.status_code in (200, 201):
            return True, "Account created successfully."

        if r.status_code == 409:
            return False, "User already exists with this email."

        return False, f"Registration failed ({r.status_code}): {r.text}"
    except Exception as e:
        return False, f"Could not reach API: {e}"


# ---------------------------
# Page
# ---------------------------
st.set_page_config(page_title="Login • Smart Energy Dashboard", layout="wide", page_icon="⚡")
_hide_sidebar_for_landing()

# session keys
if "token" not in st.session_state:
    st.session_state["token"] = None
if "api_base" not in st.session_state:
    st.session_state["api_base"] = API_DEFAULT

# If already logged in -> go to main app (relative to ui/)
if st.session_state.get("token"):
    st.switch_page("app.py")

# --- CSS  ---
st.markdown(
    """
    <style>
      .page-bg {
        background-color: #f2f7fb; /* light blue */
        padding: 24px;
        border-radius: 18px;
      }

      .split-wrap {
        width: 100%;
        border-radius: 18px;
        overflow: hidden;
        box-shadow: 0 12px 32px rgba(0,0,0,0.10);
        background: #ffffff;
      }

      .top-banner {
        height: 160px;
        width: 100%;
        background:
          linear-gradient(rgba(0,0,0,0.18), rgba(0,0,0,0.18)),
          url("https://images.unsplash.com/photo-1509391366360-2e959784a276?auto=format&fit=crop&w=2400&q=80");
        background-size: cover;
        background-position: center;
      }

      .left-panel {
        padding: 34px 32px;
        background: #ffffff;
        min-height: 520px;
      }

      .right-panel {
        padding: 34px 32px;
        background-color: #0b8f3c;
        min-height: 520px;
        color: #ffffff;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
      }

      .right-panel h2, .right-panel h3, .right-panel p, .right-panel div {
        color: #ffffff;
      }

      .icon-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 26px;
        margin-top: 26px;
        margin-bottom: 22px;
        align-items: start;
      }

      .icon-item { text-align: center; }

      .icon-circle {
        width: 66px;
        height: 66px;
        margin: 0 auto 10px auto;
        border-radius: 14px;
        display: grid;
        place-items: center;
        border: 2px solid rgba(255,255,255,0.9);
        background: rgba(255,255,255,0.06);
        font-size: 28px;
      }

      .icon-title {
        font-weight: 700;
        font-size: 0.98rem;
        margin-top: 2px;
      }

      .icon-sub {
        font-size: 0.85rem;
        opacity: 0.92;
        margin-top: 2px;
      }
      /* KPI cards base */
  .kpi-card{
    background: #ffffff;
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 16px;
    padding: 18px 18px;
    box-shadow: 0 10px 22px rgba(18,38,63,0.06);
  }

  /* Colored KPI variants */
  .kpi-card.kpi-pv { background: #FFF4DA !important; }            /* warm yellow */
  .kpi-card.kpi-consumption { background: #EAF4FF !important; }    /* light blue */
  .kpi-card.kpi-price { background: #F2EFFF !important; }          /* light purple */
  .kpi-card.kpi-self { background: #EAFBEF !important; }           /* light green */

    </style>
    """,
    unsafe_allow_html=True,
)

# ---- WRAPPERS START ----
st.markdown('<div class="page-bg">', unsafe_allow_html=True)
st.markdown('<div class="split-wrap">', unsafe_allow_html=True)
st.markdown('<div class="top-banner"></div>', unsafe_allow_html=True)

left, right = st.columns([1.05, 1.25], gap="large")

# ---------------------------
# LEFT: Login/Register
# ---------------------------
with left:


    st.markdown("## Sign In to Smart Energy ⚡")
    st.write("New here? Please register to continue.")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email address *", placeholder="user@example.com")
            password = st.text_input("Password *", type="password", placeholder="password")
            submitted = st.form_submit_button("LOGIN")

        if submitted:
            ok, msg, token = api_login(email.strip().lower(), password)
            if ok:
                st.session_state["token"] = token
                st.success("Welcome! Redirecting…")
                st.session_state["auth_email"] = email.strip().lower()
                time.sleep(0.3)
                st.switch_page("app.py")
            else:
                st.error(msg)

    with tab_register:
        with st.form("register_form", clear_on_submit=False):
            full_name = st.text_input("Full name *", placeholder="Your name")
            remail = st.text_input("Email address *", placeholder="user@example.com")
            rpassword = st.text_input("Password *", type="password", placeholder="Create a password")
            created = st.form_submit_button("CREATE ACCOUNT")

        if created:
            if not full_name.strip() or not remail.strip() or not rpassword.strip():
                st.error("Please fill Full name, Email, and Password.")
            else:
                ok, msg = api_register(remail.strip().lower(), rpassword, full_name.strip())
                if ok:
                    st.success("Account created. Now login from the Login tab.")
                else:
                    st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)  # close left-panel

# ---------------------------
# RIGHT: Overview panel
# ---------------------------
with right:
    # st.markdown('<div class="right-panel">', unsafe_allow_html=True)

    st.markdown("## Quick Overview")

    st.markdown(
        """
        <div class="icon-grid">
          <div class="icon-item">
            <div class="icon-circle">☀️</div>
            <div class="icon-title">PV</div>
            <div class="icon-sub">Hourly / Daily</div>
          </div>

          <div class="icon-item">
            <div class="icon-circle">💶</div>
            <div class="icon-title">Prices</div>
            <div class="icon-sub">EPEX AT</div>
          </div>

          <div class="icon-item">
            <div class="icon-circle">🏠</div>
            <div class="icon-title">Consumption</div>
            <div class="icon-sub">Load profile</div>
          </div>

          <div class="icon-item">
            <div class="icon-circle">🔋</div>
            <div class="icon-title">Battery</div>
            <div class="icon-sub">SOC / Flow</div>
          </div>

          <div class="icon-item">
            <div class="icon-circle">📊</div>
            <div class="icon-title">Compare</div>
            <div class="icon-sub">PV vs Load</div>
          </div>

          <div class="icon-item">
            <div class="icon-circle">✅</div>
            <div class="icon-title">Recommendations</div>
            <div class="icon-sub">Savings tips</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)  # close right-panel

# ---- WRAPPERS----
st.markdown("</div>", unsafe_allow_html=True)  # close split-wrap
st.markdown("</div>", unsafe_allow_html=True)  # close page-bg
