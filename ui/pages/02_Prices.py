# ==============================================
# File: ui/pages/02_Prices.py
# ==============================================
"""
Prices page: View market prices from CSV or API.
- Tabs: Chart | Stats | Preview
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

import pandas as pd
import requests
import streamlit as st

from utils.auth import auth_headers
from utils.theme import apply_global_style, sidebar_nav

st.set_page_config(layout="wide", page_title="Prices • Smart Energy Dashboard", page_icon="💶")

apply_global_style()
sidebar_nav(active="Prices")

if "token" not in st.session_state or not st.session_state["token"]:
    st.switch_page("pages/00_Login.py")

st.title("💶 Electricity Prices (EPEX AT)")

DATA_DIR = Path("infra/data/market")
DEFAULTS = [
    DATA_DIR / "price_2025_hourly.csv",
    DATA_DIR / "price_2026_hourly.csv",
    DATA_DIR / "price_2027_hourly.csv",
]


def infer_year_from_key(key: str) -> int | None:
    m = re.search(r"(19|20)\d{2}", key)
    return int(m.group(0)) if m else None


@st.cache_data(show_spinner=True)
def price_catalog_api(base: str) -> List[str]:
    url = f"{base}/api/v1/market/catalog"
    r = requests.get(url, timeout=10, headers=auth_headers())
    r.raise_for_status()
    data = r.json()
    return [item["key"] for item in data.get("items", [])]


@st.cache_data(show_spinner=True)
def price_range_api(base: str, key: str, start: str, end: str) -> pd.DataFrame:
    if not key:
        return pd.DataFrame()

    url = f"{base}/api/v1/market/range"
    r = requests.get(
        url,
        params={"key": key, "start": start, "end": end},
        timeout=15,
        headers=auth_headers(),
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


@st.cache_data(show_spinner=False)
def load_price_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    return df[["datetime", "price_eur_mwh"]].set_index("datetime").sort_index()


use_api = st.toggle("Use FastAPI endpoints (Default)", value=True)
api_base = st.text_input("API base", value="http://localhost:8000", disabled=not use_api)

price_df_full: pd.DataFrame | None = None

if use_api:
    try:
        series = price_catalog_api(api_base)
        if not series:
            st.error("Catalog empty")
            st.stop()

        if "price_key" not in st.session_state:
            st.session_state.price_key = series[0]

        idx = series.index(st.session_state.price_key) if st.session_state.price_key in series else 0
        st.session_state.price_key = st.selectbox("Select Price Series (API)", series, index=idx)

        # default date range follows the selected series year
        y = infer_year_from_key(st.session_state.price_key) or 2025
        d_start = pd.Timestamp(f"{y}-01-01").date()
        d_end = pd.Timestamp(f"{y}-01-07").date()

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

start_ts = pd.Timestamp(str(start), tz="UTC")
end_ts = pd.Timestamp(str(end), tz="UTC") + pd.Timedelta(days=1)

if use_api:
    try:
        sel = price_range_api(api_base, st.session_state.price_key, start_ts.isoformat(), end_ts.isoformat())
    except Exception as e:
        st.error(str(e))
        st.stop()
else:
    sel = price_df_full.loc[start_ts:end_ts] if price_df_full is not None else pd.DataFrame()

chart, stats, preview = st.tabs(["Chart", "Stats", "Preview"])

with chart:
    if sel is None or sel.empty:
        st.warning("No data available for the selected year/date range.")
    else:
        st.line_chart(sel.rename(columns={"price_eur_mwh": "€/MWh"}))

with stats:
    if sel is None or sel.empty or sel.shape[1] == 0:
        st.warning("No data available for the selected year/date range.")
    else:
        st.dataframe(sel.describe())

with preview:
    if sel is None or sel.empty:
        st.info("No rows to preview for the selected range.")
    else:
        st.dataframe(sel.head(48))
