# ui/pages/01_PV.py
"""
PV page: View PV series from CSV or API.
- Tabs: Chart | Stats | Preview
- Robust API mode for your backend:
  * /api/v1/pv/catalog -> {"items":[{"key": "...", "filename": "...", ...}, ...]}
  * /api/v1/pv/head?key=<key>&n=<n> -> {"key": "...", "count": n, "rows":[{"timestamp":"...", "value": ...}, ...]}
"""

from __future__ import annotations
import streamlit as st
import pandas as pd
from pathlib import Path
import requests
from typing import List

st.set_page_config(page_title="PV • Smart Energy Dashboard", layout="wide")

import streamlit as st

if "token" not in st.session_state or not st.session_state["token"]:
    st.switch_page("pages/00_Login.py")

    
st.title("☀️ PV Production")


DATA_DIR = Path("infra/data/pv")
DEFAULTS = [
    DATA_DIR / "pv_2025_hourly.csv",
    DATA_DIR / "pv_2026_hourly.csv",
    DATA_DIR / "pv_2027_hourly.csv",
]

use_api = st.toggle(
    "Use FastAPI endpoints (Default)",
    value=True,
    help="/api/v1/pv/... must be running on localhost:8000",
)
if "api_base" not in st.session_state:
    st.session_state["api_base"] = "http://localhost:8000"

st.session_state["api_base"] = st.text_input(
    "API base",
    value=st.session_state["api_base"],
    disabled=not use_api,
)
api_base = st.session_state["api_base"]

@st.cache_data(show_spinner=False)
def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Normalize time column
    if "datetime" not in df.columns:
        if "timestamp" in df.columns:
            df = df.rename(columns={"timestamp": "datetime"})
        else:
            raise KeyError(f"CSV '{path}' must have a 'datetime' column. Columns: {list(df.columns)}")
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)

    # Normalize value column (prefer energy kWh; convert kW->kWh for hourly)
    value_col: str
    if "production_kwh" in df.columns:
        value_col = "production_kwh"
    elif "production_kw" in df.columns:
        df["production_kwh"] = pd.to_numeric(df["production_kw"], errors="coerce").astype("float64") * 1.0
        value_col = "production_kwh"
    else:
        if len(df.columns) <= 1:
            raise KeyError(f"Could not detect PV value column in '{path}'. Columns: {list(df.columns)}")
        # fall back to the second column but enforce str typing
        fallback = str(df.columns[1])
        value_col = fallback

    return (
        df[["datetime", value_col]]
        .set_index("datetime")
        .rename(columns={value_col: "production_kwh"})
        .sort_index()
    )

@st.cache_data(show_spinner=True)
def pv_catalog_api(base: str) -> List[str]:
    """
    Parse catalog of the form:
      {"items":[{"key":"pv_2025_hourly","filename":"pv_2025_hourly.csv", ...}, ...]}
    Return list of keys.
    """
    url = f"{base}/api/v1/pv/catalog"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and "items" in data and isinstance(data["items"], list):
        keys = [str(item.get("key", "")) for item in data["items"] if item.get("key")]
        return keys
    # Fallbacks (older shapes)
    if isinstance(data, dict) and "series" in data and isinstance(data["series"], list):
        return [str(x) for x in data["series"]]
    if isinstance(data, list):
        return [str(x) for x in data]
    return []

@st.cache_data(show_spinner=True)
def pv_range_api(base: str, key: str, start: str, end: str) -> pd.DataFrame:
    """
    GET /api/v1/pv/range?key=...&start=...&end=...
    """
    if not key:
        return pd.DataFrame()
    
    url = f"{base}/api/v1/pv/range"
    params = [("key", key), ("start", start), ("end", end)]
    
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    rows = data.get("rows", [])
    df = pd.DataFrame(rows)

    if df.empty:
        return df

    # Normalize columns
    if "datetime" in df.columns:
        ts_col = "datetime"
    elif "timestamp" in df.columns:
        ts_col = "timestamp"
    else:
        # Fallback if empty or malformed
        return df

    # Value column mapping
    if "value" in df.columns:
        val_col = "value"
    elif "production_kwh" in df.columns:
        val_col = "production_kwh"
    else:
        # Check for numeric fallback
        num = [c for c in df.columns if c != ts_col and pd.api.types.is_numeric_dtype(df[c])]
        val_col = num[0] if num else df.columns[-1]

    df[ts_col] = pd.to_datetime(df[ts_col], utc=True)
    df = df.rename(columns={ts_col: "datetime", val_col: "production_kwh"})
    return df.set_index("datetime")[["production_kwh"]].sort_index()

# --- Main Logic ---

pv_df_full = None  # Setup for CSV mode
api_defaults = (pd.date_range("2025-01-01", periods=1).date[0], pd.date_range("2025-01-07", periods=1).date[0])

if use_api:
    try:
        series = pv_catalog_api(api_base)
        if not series:
            st.error("Catalog is empty.")
            st.stop()

        if "pv_key" not in st.session_state:
            st.session_state.pv_key = series[0]

        idx = series.index(st.session_state.pv_key) if st.session_state.pv_key in series else 0
        st.session_state.pv_key = st.selectbox("Select PV series (API)", options=series, index=idx)
        
        # API Defaults
        d_start, d_end = api_defaults
    except Exception as e:
        st.error(f"API Error: {e}")
        st.stop()
else:
    files = [str(p) for p in DEFAULTS if p.exists()]
    pv_path = st.selectbox("PV CSV", options=files or ["<missing>"])
    if pv_path == "<missing>":
        st.warning("No PV CSVs found")
        st.stop()
    pv_df_full = load_csv(pv_path)
    if not pv_df_full.empty:
        d_start = pv_df_full.index.min().date()
        d_end = min(pv_df_full.index.min().date() + pd.Timedelta(days=7), pv_df_full.index.max().date())
    else:
        d_start, d_end = api_defaults

# Date Selection
left, right = st.columns(2)
with left:
    start = st.date_input("Start", value=d_start)
with right:
    end = st.date_input("End", value=d_end)

# Fetch Data
start_ts_iso = pd.Timestamp(str(start)).isoformat()
end_ts_iso = (pd.Timestamp(str(end)) + pd.Timedelta(days=1)).isoformat()

if use_api:
    try:
        pv_sel = pv_range_api(api_base, st.session_state.pv_key, start_ts_iso, end_ts_iso)
    except Exception as e:
        st.error(f"API Fetch Failed: {e}")
        st.stop()
else:
    start_ts = pd.Timestamp(str(start), tz="UTC")
    end_ts = pd.Timestamp(str(end), tz="UTC") + pd.Timedelta(days=1)
    if pv_df_full is not None:
        pv_sel = pv_df_full.loc[start_ts:end_ts]
    else:
        pv_sel = pd.DataFrame()

chart, stats, preview = st.tabs(["Chart", "Stats", "Preview"])
with chart:
    st.line_chart(pv_sel.rename(columns={"production_kwh": "PV (kWh)"}))
with stats:
    st.dataframe(pv_sel.describe())
with preview:
    st.dataframe(pv_sel.head(48))