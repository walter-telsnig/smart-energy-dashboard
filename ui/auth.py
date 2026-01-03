# ui/auth.py
from __future__ import annotations

import time
import requests
import streamlit as st
from dataclasses import dataclass
import xml.etree.ElementTree as ET


API_DEFAULT = "http://localhost:8000"

TOKEN_KEY = "token"
EMAIL_KEY = "auth_email"
API_BASE_KEY = "api_base"


@dataclass
class AuthResult:
    ok: bool
    message: str = ""
    token: str = ""


def _api_base() -> str:
    return str(st.session_state.get(API_BASE_KEY, API_DEFAULT)).rstrip("/")


def _set_token(token: str, email: str) -> None:
    st.session_state[TOKEN_KEY] = token
    st.session_state[EMAIL_KEY] = email


def is_logged_in() -> bool:
    return bool(st.session_state.get(TOKEN_KEY))


def logout() -> None:
    st.session_state[TOKEN_KEY] = None
    st.session_state[EMAIL_KEY] = None


def require_login() -> None:
    if not is_logged_in():
        st.warning("Please log in to access this page.")
        st.stop()


def api_login(email: str, password: str) -> AuthResult:
    base = _api_base()
    url = f"{base}/api/v1/token"
    try:
        r = requests.post(
            url,
            data={"username": email, "password": password},
            timeout=10,
        )
        if r.status_code != 200:
            return AuthResult(False, f"Login failed ({r.status_code}): {r.text}")

        data = r.json()
        token = data.get("access_token")
        if not token:
            return AuthResult(False, "Login response missing access_token")
        return AuthResult(True, "Logged in", token=token)
    except Exception as e:
        return AuthResult(False, f"Could not reach API: {e}")


def api_register(email: str, password: str, full_name: str) -> AuthResult:
    base = _api_base()
    url = f"{base}/api/v1/accounts/"
    try:
        r = requests.post(
            url,
            json={"email": email, "password": password, "full_name": full_name},
            timeout=10,
        )
        if r.status_code in (200, 201):
            return AuthResult(True, "Account created successfully.")
        if r.status_code == 409:
            return AuthResult(False, "User already exists.")
        return AuthResult(False, f"Registration failed ({r.status_code}): {r.text}")
    except Exception as e:
        return AuthResult(False, f"Could not reach API: {e}")


def _hide_sidebar() -> None:
    st.markdown(
        """
        <style>
          section[data-testid="stSidebar"] { display: none !important; }
          button[kind="header"] { display: none !important; }
          .block-container { padding-top: 2rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _meta_refresh(seconds: int = 60) -> None:
    st.markdown(
        f'<meta http-equiv="refresh" content="{int(seconds)}">', unsafe_allow_html=True
    )


def _fetch_rss_titles(url: str, limit: int = 6) -> list[str]:
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        titles: list[str] = []
        for item in root.findall(".//item/title"):
            if item.text:
                titles.append(item.text.strip())
            if len(titles) >= limit:
                break
        return titles
    except Exception:
        return []


def _fetch_live_kpis() -> dict:
    base = _api_base()
    url = f"{base}/api/v1/timeseries/merged?hours=1&window=true"
    out = {"pv": 0.0, "load": 0.0, "price": 0.0}
    try:
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            data = r.json()
            if data:
                row = data[0]
                out["pv"] = float(row.get("pv_kwh", 0) or 0)
                out["load"] = float(row.get("load_kwh", 0) or 0)
                out["price"] = float(row.get("price_eur_kwh", 0) or 0)
    except Exception:
        pass
    return out


def render_login_page() -> None:
    """
    Call this ONLY from ui/pages/00_Login.py
    """
    _hide_sidebar()
    _meta_refresh(60)

    if API_BASE_KEY not in st.session_state:
        st.session_state[API_BASE_KEY] = API_DEFAULT

    st.markdown(
        """
        <style>
          .login-wrap {
            background: linear-gradient(rgba(0,0,0,0.25), rgba(0,0,0,0.25)),
                        url("https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=2400&q=80");
            background-size: cover;
            background-position: center;
            padding: 48px 32px;
            border-radius: 18px;
          }
          .panel {
            background: rgba(255,255,255,0.93);
            border-radius: 12px;
            padding: 26px 26px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.18);
          }
          .green {
            background: #0a8f3c;
            border-radius: 12px;
            padding: 26px 26px;
            color: white;
            box-shadow: 0 8px 24px rgba(0,0,0,0.18);
            min-height: 420px;
          }
          .green h2, .green h3, .green p { color: white; }
          .muted { color: rgba(255,255,255,0.85); }
          .small { font-size: 0.9rem; opacity: 0.9; }
          .kpi { display:flex; gap:18px; margin-top:14px; flex-wrap:wrap; }
          .kpi div {
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.18);
            padding: 12px 14px;
            border-radius: 10px;
            min-width: 140px;
          }
          .kpi .v { font-size: 1.3rem; font-weight: 700; }
          .kpi .l { font-size: 0.85rem; opacity: 0.9; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, main, _ = st.columns([1, 3, 1])
    with main:
        st.markdown('<div class="login-wrap">', unsafe_allow_html=True)

        left, right = st.columns([1.1, 1.4], gap="large")

        with left:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown("## Welcome")
            st.write("Sign in to continue, or create a new account.")

            tab_login, tab_register = st.tabs(["Login", "Register"])

            with tab_login:
                with st.form("login_form", clear_on_submit=False):
                    email = st.text_input("Email *", placeholder="user@example.com")
                    password = st.text_input(
                        "Password *", type="password", placeholder="password"
                    )
                    submitted = st.form_submit_button("LOGIN")

                if submitted:
                    res = api_login(email.strip(), password)
                    if res.ok:
                        _set_token(res.token, email.strip().lower())
                        st.success("Welcome! Redirecting…")
                        time.sleep(0.4)
                        st.switch_page("ui/app.py")
                    else:
                        st.error(res.message)

            with tab_register:
                with st.form("register_form", clear_on_submit=False):
                    full_name = st.text_input("Full name *", placeholder="Your name")
                    remail = st.text_input("Email *", placeholder="user@example.com")
                    rpassword = st.text_input(
                        "Password *", type="password", placeholder="Create a password"
                    )
                    created = st.form_submit_button("CREATE ACCOUNT")

                if created:
                    res = api_register(remail.strip(), rpassword, full_name.strip())
                    if res.ok:
                        st.success("Account created. Now log in from the Login tab.")
                    else:
                        st.error(res.message)

            st.caption("Optional: configure API base (usually keep default).")
            st.session_state[API_BASE_KEY] = st.text_input(
                "API Base",
                value=str(st.session_state[API_BASE_KEY]),
                help="Example: http://localhost:8000",
            ).rstrip("/")

            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown('<div class="green">', unsafe_allow_html=True)
            st.markdown("## Everything at a glance")
            st.markdown(
                '<p class="muted">A quick snapshot that refreshes automatically.</p>',
                unsafe_allow_html=True,
            )

            kpis = _fetch_live_kpis()
            st.markdown(
                f"""
                <div class="kpi">
                  <div><div class="v">{kpis['pv']:.2f}</div><div class="l">PV (kWh, last hour)</div></div>
                  <div><div class="v">{kpis['load']:.2f}</div><div class="l">Load (kWh, last hour)</div></div>
                  <div><div class="v">{kpis['price']:.3f}</div><div class="l">Price (€/kWh)</div></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("### Today")
            st.caption("Auto-updates every minute.")

            rss_url = "https://feeds.bbci.co.uk/news/world/rss.xml"
            titles = _fetch_rss_titles(rss_url, limit=6)
            if titles:
                for t in titles:
                    st.write("•", t)
            else:
                st.write("• No news feed available.")

            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
