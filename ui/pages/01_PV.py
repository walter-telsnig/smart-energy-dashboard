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
from typing import List, Tuple

st.set_page_config(layout="wide")
st.title("☀️ PV Production")

DATA_DIR = Path("infra/data/pv")
DEFAULTS = [
    DATA_DIR / "pv_2025_hourly.csv",
    DATA_DIR / "pv_2026_hourly.csv",
    DATA_DIR / "pv_2027_hourly.csv",
]

use_api = st.toggle(
    "Use FastAPI endpoints instead of CSV",
    value=False,
    help="/api/v1/pv/... must be running on localhost:8000",
)
api_base = st.text_input("API base", value="http://localhost:8000", disabled=not use_api)

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
    if "production_kwh" in df.columns:
        value_col = "production_kwh"
    elif "production_kw" in df.columns:
        df["production_kwh"] = pd.to_numeric(df["production_kw"], errors="coerce").astype("float64") * 1.0
        value_col = "production_kwh"
    else:
        # Fallback to next column if present
        value_col = df.columns[1] if len(df.columns) > 1 else None
        if value_col is None:
            raise KeyError(f"Could not detect PV value column in '{path}'. Columns: {list(df.columns)}")

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
def pv_head_api(base: str, key: str, n: int) -> pd.DataFrame:
    """
    GET /api/v1/pv/head?key=<key>&n=<n>
    Expects:
      {"key":"...", "count": n, "rows":[{"timestamp":"...", "value": ...}, ...]}
    """
    if not key:
        raise ValueError("No PV series key selected.")
    url = f"{base}/api/v1/pv/head"
    # Use a typed list of tuples to please mypy/requests typing
    params: List[Tuple[str, str]] = [("key", key), ("n", str(int(n)))]
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    rows = data.get("rows", data)
    df = pd.DataFrame(rows)

    # Accept both 'timestamp' and 'datetime'
    if "datetime" in df.columns:
        ts_col = "datetime"
    elif "timestamp" in df.columns:
        ts_col = "timestamp"
    else:
        raise KeyError(f"API response missing 'timestamp'/'datetime' field: {df.columns.tolist()}")

    # Accept 'value' or 'production_kwh' or convert 'production_kw' -> kWh
    if "value" in df.columns:
        val_col = "value"
    elif "production_kwh" in df.columns:
        val_col = "production_kwh"
    elif "production_kw" in df.columns:
        df["production_kwh"] = pd.to_numeric(df["production_kw"], errors="coerce").astype("float64") * 1.0
        val_col = "production_kwh"
    else:
        raise KeyError(f"API response missing 'value'/'production_kwh' field: {df.columns.tolist()}")

    df[ts_col] = pd.to_datetime(df[ts_col], utc=True)
    df = df.rename(columns={ts_col: "datetime", val_col: "production_kwh"})
    return df.set_index("datetime")[["production_kwh"]].sort_index()

if use_api:
    try:
        series = pv_catalog_api(api_base)
        if not series:
            st.error("Catalog is empty or unrecognized. Check /api/v1/pv/catalog response.")
            st.stop()

        # Keep selection stable across reruns
        if "pv_key" not in st.session_state:
            st.session_state.pv_key = series[0]

        default_idx = series.index(st.session_state.pv_key) if st.session_state.pv_key in series else 0
        st.session_state.pv_key = st.selectbox("Select PV series (API)", options=series, index=default_idx)

        n = st.slider("Initial rows to preview", 24, 24*30, 24*7, step=24)
        pv = pv_head_api(api_base, st.session_state.pv_key, n)
    except requests.HTTPError as http_err:
        st.error(f"API error: {http_err}")
        st.stop()
    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()
else:
    files = [str(p) for p in DEFAULTS if p.exists()]
    pv_path = st.selectbox("PV CSV", options=files or ["<missing>"])
    if pv_path == "<missing>":
        st.warning("No PV CSVs found in infra/data/pv")
        st.stop()
    pv = load_csv(pv_path)

# Date selection
left, right = st.columns(2)
with left:
    start = st.date_input("Start", value=pv.index.min().date())
with right:
    end = st.date_input("End", value=min(pv.index.min().date() + pd.Timedelta(days=7), pv.index.max().date()))

start_ts = pd.Timestamp(start, tz="UTC")
end_ts = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
pv_sel = pv.loc[start_ts:end_ts]

chart, stats, preview = st.tabs(["Chart", "Stats", "Preview"])
with chart:
    st.line_chart(pv_sel.rename(columns={"production_kwh": "PV (kWh)"}))
with stats:
    st.dataframe(pv_sel.describe())
with preview:
    st.dataframe(pv_sel.head(48))
