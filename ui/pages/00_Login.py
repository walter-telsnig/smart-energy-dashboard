# ui/pages/00_Login.py
from __future__ import annotations

import time
import requests
import streamlit as st

API_DEFAULT = "http://localhost:8000"


def _hide_sidebar_for_landing() -> None:
    st.markdown(
        """
        <style>
          section[data-testid="stSidebar"] { display: none !important; }
          button[kind="header"] { display: none !important; }

          .block-container {
            padding-top: 1.8rem;
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


st.set_page_config(page_title="Login • Smart Energy Dashboard", layout="wide", page_icon="⚡")
_hide_sidebar_for_landing()

if "token" not in st.session_state:
    st.session_state["token"] = None
if "api_base" not in st.session_state:
    st.session_state["api_base"] = API_DEFAULT
if "show_forgot" not in st.session_state:
    st.session_state["show_forgot"] = False

if st.session_state.get("token"):
    st.switch_page("app.py")

st.markdown(
    """
    <style>
      /*  modern background */
      .stApp {
        background:
          radial-gradient(1200px 650px at 15% 10%, rgba(34,197,94,0.11), transparent 60%),
          radial-gradient(1000px 650px at 85% 25%, rgba(59,130,246,0.12), transparent 55%),
          radial-gradient(900px 650px at 65% 95%, rgba(168,85,247,0.10), transparent 60%),
          linear-gradient(135deg, #f7fbff 0%, #f4f7ff 45%, #f8f6ff 100%);
      }

      .split-wrap {
        width: 100%;
        border-radius: 18px;
        overflow: hidden;
        box-shadow: 0 14px 34px rgba(18,38,63,0.10);
        background: rgba(255,255,255,0.75);
        backdrop-filter: blur(10px);
      }

      .top-banner {
        height: 220px;
        width: 100%;
        background:
          linear-gradient(90deg, rgba(2,6,23,0.55), rgba(2,6,23,0.12)),
          url("https://images.unsplash.com/photo-1509391366360-2e959784a276?auto=format&fit=crop&w=2400&q=80");
        background-size: cover;
        background-position: center;
      }

      /*  Equal-height panels */
      .panel {
        height: 6000px;
        border-radius: 12px;
        padding: 24px 32px;
      }

      .left-panel {
        background: rgba(255,255,255,0.86);
        border: 1px solid rgba(2,6,23,0.06);
      }

      .right-panel {
        background:
          radial-gradient(900px 520px at 20% 15%, rgba(34,197,94,0.22), transparent 55%),
          radial-gradient(900px 520px at 90% 35%, rgba(59,130,246,0.20), transparent 55%),
          linear-gradient(180deg, rgba(2,6,23,0.86), rgba(2,6,23,0.78));
        border: 1.5px solid rgba(255,255,255,0.10);
        color: #ffffff;
      }

      .right-panel * { color: #ffffff; }

      .right-title {
        text-align: center;
        font-weight: 900;
        font-size: 1.9rem;
        margin: 2 2 6px 2;
        margin-top: 15px;
      }

      .right-sub {
        text-align: center;
        opacity: 1;
        margin-bottom: 25px;
      }

      .icon-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 22px;
        margin-top: 35px;
      }

      .icon-item { text-align: center; }

      .icon-circle {
        width: 66px;
        height: 66px;
        margin: 0 auto 10px auto;
        border-radius: 16px;
        display: grid;
        place-items: center;
        border: 1px solid rgba(255,255,255,0.24);
        background: rgba(255,255,255,0.10);
        font-size: 28px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.20);
      }

      .icon-title { font-weight: 900; font-size:1rem; margin-top: 20px;}
      .icon-sub { font-size: 1 rem; opacity: 0.86; margin-top: 15px;}

      /* Buttons */
      div.stButton > button { border-radius: 12px !important; font-weight: 750 !important; }
      .fp-btn button {
        background: transparent !important;
        border: 1px solid rgba(2,6,23,0.18) !important;
      }
      .fp-btn button:hover {
        border-color: rgba(2,6,23,0.30) !important;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="split-wrap">', unsafe_allow_html=True)
st.markdown('<div class="top-banner"></div>', unsafe_allow_html=True)

left, right = st.columns([1.05, 1.25], gap="large")

# LEFT
with left:

    st.markdown("## Sign In to Smart Energy ⚡")
    st.write("New here? Please register to continue.")

    tab_login, tab_register = st.tabs(["Login", "Register"])

    with tab_login:
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email address *", placeholder="user@example.com")
            password = st.text_input("Password *", type="password", placeholder="password")

            #  LOGIN + FORGOT password 
            c1, c2 = st.columns([1, 1])
            with c1:
                submitted = st.form_submit_button("LOGIN", type="primary")
            with c2:
                st.markdown('<div class="fp-btn">', unsafe_allow_html=True)
                forgot_clicked = st.form_submit_button("Forgot password?")
                st.markdown("</div>", unsafe_allow_html=True)

        if forgot_clicked:
            st.session_state["show_forgot"] = True

        if st.session_state["show_forgot"]:
            with st.expander("Reset your password", expanded=True):
                fp_email = st.text_input("Enter your registered email", key="fp_email")
                if st.button("Send reset link", key="fp_send"):
                    st.success(
                        "If an account exists for this email, a reset link will be sent shortly. "
                        "(Email delivery will be enabled once backend email service is connected.)"
                    )

        if submitted:
            ok, msg, token = api_login(email.strip().lower(), password)
            if ok:
                st.session_state["token"] = token
                st.session_state["auth_email"] = email.strip().lower()
                st.success("Welcome! Redirecting…")
                time.sleep(0.25)
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
                    st.success(
                        "✅ Successfully registered! You can now log in. "
                        "Email confirmation will be enabled once the email service is connected."
                    )
                else:
                    st.error(msg)

    st.markdown("</div>", unsafe_allow_html=True)

# RIGHT
with right:

    st.markdown('<div class="right-title">Overview</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="right-sub">PV • Prices • Consumption • Battery • Compare • Recommendations</div>',
        unsafe_allow_html=True,
    )

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

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # split-wrap end