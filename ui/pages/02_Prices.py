# ==============================================
# File: ui/pages/02_Prices.py
# ==============================================
"""
Prices page: View market prices from CSV.
- Tabs: Chart | Stats | Preview
"""

from __future__ import annotations
import streamlit as st
import pandas as pd
import requests
from typing import List
from pathlib import Path
from utils.theme import apply_global_style, sidebar_nav
from utils.auth import auth_headers

st.set_page_config(
    layout="wide", page_title="Prices • Smart Energy Dashboard", page_icon="💶"
)

apply_global_style()
sidebar_nav(active="Prices")

if "token" not in st.session_state or not st.session_state["token"]:
    st.switch_page("pages/00_Login.py")


def _auth_headers() -> dict:
    tok = st.session_state.get("token")
    return {"Authorization": f"Bearer {tok}"} if tok else {}


if "token" not in st.session_state or st.session_state["token"] is None:
    st.warning("Please log in to access this page.")
    st.stop()
st.title("💶 Electricity Prices (EPEX AT)")

DATA_DIR = Path("infra/data/market")
DEFAULTS = [
    DATA_DIR / "price_2025_hourly.csv",
    DATA_DIR / "price_2026_hourly.csv",
    DATA_DIR / "price_2027_hourly.csv",
]


# --- API Client ---
@st.cache_data(show_spinner=True)
def price_catalog_api(base: str) -> List[str]:
    url = f"{base}/api/v1/market/catalog"
    r = requests.get(
        url,
        timeout=10,
        headers=auth_headers(),
    )
    r.raise_for_status()
    data = r.json()
    return [item["key"] for item in data.get("items", [])]


@st.cache_data(show_spinner=True)
def price_range_api(base: str, key: str, start: str, end: str) -> pd.DataFrame:
    if not key:
        return pd.DataFrame()
    url = f"{base}/api/v1/market/range"
    # r = requests.get(url, params={"key": key, "start": start, "end": end}, timeout=10)
    r = requests.get(
        url,
        params={"key": key, "start": start, "end": end},
        timeout=15,
        headers=auth_headers(),  # JWT header
    )
    r.raise_for_status()
    rows = r.json().get("rows", [])
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return (
        df.rename(columns={"timestamp": "datetime", "value": "price_eur_mwh"})
        .set_index("datetime")
        .sort_index()
    )


# --- CSV Client ---
@st.cache_data(show_spinner=False)
def load_price_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    return df[["datetime", "price_eur_mwh"]].set_index("datetime").sort_index()


# --- UI ---
use_api = st.toggle("Use FastAPI endpoints (Default)", value=True)
api_base = st.text_input(
    "API base", value="http://localhost:8000", disabled=not use_api
)

price_df_full = None
api_defaults = (
    pd.date_range("2025-01-01", periods=1).date[0],
    pd.date_range("2025-01-07", periods=1).date[0],
)

if use_api:
    try:
        series = price_catalog_api(api_base)
        if not series:
            st.error("Catalog empty")
            st.stop()
        if "price_key" not in st.session_state:
            st.session_state.price_key = series[0]
        idx = (
            series.index(st.session_state.price_key)
            if st.session_state.price_key in series
            else 0
        )
        st.session_state.price_key = st.selectbox(
            "Select Price Series (API)", series, index=idx
        )
        d_start, d_end = api_defaults
    except Exception as e:
        st.error(f"API Error: {e}")
        st.stop()
else:
    files = [str(p) for p in DEFAULTS if p.exists()]
    price_path = st.selectbox("Price CSV", options=files or ["<missing>"])
    if price_path == "<missing>":
        st.warning("No CSVs found")
        st.stop()
    price_df_full = load_price_csv(price_path)
    d_start = price_df_full.index.min().date()
    d_end = min(
        price_df_full.index.min().date() + pd.Timedelta(days=7),
        price_df_full.index.max().date(),
    )

left, right = st.columns(2)
with left:
    start = st.date_input("Start", value=d_start)
with right:
    end = st.date_input("End", value=d_end)

if use_api:
    try:
        sel = price_range_api(
            api_base,
            st.session_state.price_key,
            pd.Timestamp(str(start)).isoformat(),
            (pd.Timestamp(str(end)) + pd.Timedelta(days=1)).isoformat(),
        )
    except Exception as e:
        st.error(str(e))
        st.stop()
else:
    if price_df_full is not None:
        sel = price_df_full.loc[
            pd.Timestamp(str(start), tz="UTC") : pd.Timestamp(str(end), tz="UTC")
            + pd.Timedelta(days=1)
        ]
    else:
        sel = pd.DataFrame()

chart, stats, preview = st.tabs(["Chart", "Stats", "Preview"])
with chart:
    st.line_chart(sel.rename(columns={"price_eur_mwh": "€/MWh"}))
with stats:
    st.dataframe(sel.describe())
with preview:
    st.dataframe(sel.head(48))
