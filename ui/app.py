# ==============================================
# File: ui/app.py
# ==============================================
from __future__ import annotations

import requests
import pandas as pd
import streamlit as st
from utils.theme import apply_global_style, sidebar_nav

st.set_page_config(layout="wide", page_title="Smart Energy Dashboard", page_icon="⚡")

apply_global_style()
sidebar_nav(active="Dashboard")

API_DEFAULT = "http://localhost:8000"


# ---------------------------
# Auth gate
# ---------------------------
if "token" not in st.session_state:
    st.session_state["token"] = None

if "api_base" not in st.session_state:
    st.session_state["api_base"] = API_DEFAULT

if not st.session_state["token"]:
    st.switch_page("pages/00_Login.py")


def _api_base() -> str:
    return str(st.session_state.get("api_base", API_DEFAULT)).rstrip("/")


def _auth_headers() -> dict:
    tok = st.session_state.get("token")
    return {"Authorization": f"Bearer {tok}"} if tok else {}


@st.cache_data(ttl=15, show_spinner=False)
def fetch_merged(hours: int = 24) -> pd.DataFrame:
    base = _api_base()
    url = f"{base}/api/v1/timeseries/merged"
    r = requests.get(
        url,
        params={"hours": hours, "window": "true"},
        timeout=5,
        headers=_auth_headers(),
    )
    r.raise_for_status()
    data = r.json()
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    ts_col = None
    if "timestamp" in df.columns:
        ts_col = "timestamp"
    elif "datetime" in df.columns:
        ts_col = "datetime"

    if ts_col:
        df[ts_col] = pd.to_datetime(df[ts_col], utc=True)
        df = df.rename(columns={ts_col: "datetime"}).set_index("datetime").sort_index()

    keep = [
        c
        for c in ["pv_kwh", "load_kwh", "price_eur_kwh", "price_eur_mwh"]
        if c in df.columns
    ]
    return df[keep] if keep else df


# ---------------------------
# Styling
# ---------------------------
st.markdown(
    """
    <style>
      [data-testid="stSidebarNav"] { display: none !important; }
      [data-testid="stSidebarNavItems"] { display: none !important; }

      section[data-testid="stSidebar"] {
        background: #0b2a4a !important;
        border-right: 1px solid rgba(255,255,255,0.08);
      }
      section[data-testid="stSidebar"] * {
        color: #eaf2ff !important;
      }
      section[data-testid="stSidebar"] .block-container {
        padding-top: 1.2rem;
        padding-bottom: 1.2rem;
      }

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
        margin-top: 0.8rem;
        margin-bottom: 0.35rem;
        font-size: 0.78rem;
        letter-spacing: 0.14em;
        opacity: 0.75;
        font-weight: 800;
        text-transform: uppercase;
      }

      section[data-testid="stSidebar"] .stButton>button {
        width: 100%;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(255,255,255,0.06);
        padding: 0.70rem 0.85rem;
        text-align: left;
        font-weight: 650;
      }
      section[data-testid="stSidebar"] .stButton>button:hover {
        background: rgba(255,255,255,0.12);
        border-color: rgba(255,255,255,0.18);
      }

      .kpi-card {
        background: white;
        border: 1px solid rgba(0,0,0,0.06);
        border-radius: 16px;
        padding: 14px 16px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.06);
      }
      .kpi-title { font-size: 0.85rem; opacity: 0.75; margin-bottom: 6px; }
      .kpi-value { font-size: 1.55rem; font-weight: 800; line-height: 1.1; }
      .kpi-sub { margin-top: 6px; font-size: 0.85rem; opacity: 0.75; }

      .section-card {
        background: white;
        border: 1px solid rgba(0,0,0,0.06);
        border-radius: 16px;
        padding: 16px 16px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.06);
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------
# Sidebar Navigation
# ---------------------------
with st.sidebar:
    view_mode = st.session_state.get("view_mode", "Hourly View")
# ---------------------------
# Main Dashboard (highlights)
# ---------------------------
st.markdown("# Dashboard Overview")
st.caption("Highlights + trends. Use the left navigation to open full modules.")

try:
    df = fetch_merged(hours=24)
except Exception as e:
    st.warning(f"Could not load live highlights from API. ({e})")
    df = pd.DataFrame()

if df.empty:
    st.info(
        "No merged data available yet. Start the API and ensure /api/v1/timeseries/merged returns rows."
    )
    st.stop()

# Daily vs Hourly
if view_mode == "Daily View":
    agg = {}
    if "pv_kwh" in df.columns:
        agg["pv_kwh"] = "sum"
    if "load_kwh" in df.columns:
        agg["load_kwh"] = "sum"
    if "price_eur_kwh" in df.columns:
        agg["price_eur_kwh"] = "mean"
    if "price_eur_mwh" in df.columns:
        agg["price_eur_mwh"] = "mean"
    df_viz = df.resample("1D").agg(agg).dropna(how="all")
else:
    df_viz = df

latest = df.iloc[-1].to_dict() if len(df) else {}
pv = float(latest.get("pv_kwh", 0) or 0)
load = float(latest.get("load_kwh", 0) or 0)

price = 0.0
if "price_eur_kwh" in df.columns:
    price = float(latest.get("price_eur_kwh", 0) or 0)
elif "price_eur_mwh" in df.columns:
    price = float(latest.get("price_eur_mwh", 0) or 0) / 1000.0

self_suff = (min(pv, load) / load * 100.0) if load > 0 else 100.0
grid_flow = load - pv

delta_pv = delta_load = delta_price = 0.0
if len(df) >= 2:
    prev = df.iloc[-2].to_dict()
    delta_pv = pv - float(prev.get("pv_kwh", 0) or 0)
    delta_load = load - float(prev.get("load_kwh", 0) or 0)
    if "price_eur_kwh" in df.columns:
        delta_price = price - float(prev.get("price_eur_kwh", 0) or 0)
    elif "price_eur_mwh" in df.columns:
        delta_price = price - (float(prev.get("price_eur_mwh", 0) or 0) / 1000.0)

k1, k2, k3, k4 = st.columns(4, gap="large")
with k1:
    st.markdown(
        f"""
        <div class="kpi-card kpi-pv">
          <div class="kpi-title">PV (latest)</div>
          <div class="kpi-value">{pv:.2f} kWh</div>
          <div class="kpi-sub">Δ {delta_pv:+.2f} vs prev</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k2:
    st.markdown(
        f"""
        <div class="kpi-card kpi-consumption">
          <div class="kpi-title">Consumption (latest)</div>
          <div class="kpi-value">{load:.2f} kWh</div>
          <div class="kpi-sub">Δ {delta_load:+.2f} vs prev</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k3:
    st.markdown(
        f"""
        <div class="kpi-card kpi-price">
          <div class="kpi-title">Price (latest)</div>
          <div class="kpi-value">{price:.4f} €/kWh</div>
          <div class="kpi-sub">Δ {delta_price:+.4f} vs prev</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with k4:
    st.markdown(
        f"""
        <div class="kpi-card kpi-self">
          <div class="kpi-title">Self-sufficiency</div>
          <div class="kpi-value">{self_suff:.1f}%</div>
          <div class="kpi-sub">Grid balance: {grid_flow:+.2f} kWh</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("")

c1, c2 = st.columns([1.2, 1], gap="large")

with c1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader(
        f"PV vs Consumption ({'daily' if view_mode=='Daily View' else 'hourly'} trend)"
    )
    cols = [c for c in ["pv_kwh", "load_kwh"] if c in df_viz.columns]
    if cols:
        st.line_chart(df_viz[cols])
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader(
        f"Price trend ({'daily' if view_mode=='Daily View' else 'hourly'} trend)"
    )
    if "price_eur_kwh" in df_viz.columns:
        st.line_chart(
            df_viz[["price_eur_kwh"]].rename(columns={"price_eur_kwh": "€/kWh"})
        )
    elif "price_eur_mwh" in df_viz.columns:
        st.line_chart(
            df_viz[["price_eur_mwh"]].rename(columns={"price_eur_mwh": "€/MWh"})
        )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.subheader("Quick data preview (latest 12 rows)")
st.dataframe(df.tail(12), use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)
