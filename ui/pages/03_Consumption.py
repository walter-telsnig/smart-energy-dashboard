# ==============================================
# File: ui/pages/03_Consumption.py
# ==============================================
"""
Consumption page: View household load from CSV.
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

st.set_page_config(
    layout="wide", page_title="Consumption • Smart Energy Dashboard", page_icon="🏠"
)

apply_global_style()
sidebar_nav(active="Consumption")

# --- Auth guard ---
if "token" not in st.session_state or not st.session_state["token"]:
    st.switch_page("pages/00_Login.py")

st.title("🏠 Household Consumption")

DATA_DIR = Path("infra/data/consumption")
DEFAULTS = [
    DATA_DIR / "consumption_2025_hourly.csv",
    DATA_DIR / "consumption_2026_hourly.csv",
    DATA_DIR / "consumption_2027_hourly.csv",
]


def infer_year_from_key(key: str) -> int | None:
    """Extract YYYY from a series key like 'consumption_2026_hourly'."""
    m = re.search(r"(19|20)\d{2}", key)
    return int(m.group(0)) if m else None


# --- API Client ---
@st.cache_data(show_spinner=True)
def cons_catalog_api(base: str) -> List[str]:
    url = f"{base}/api/v1/consumption/catalog"
    r = requests.get(url, timeout=10, headers=auth_headers())
    r.raise_for_status()
    data = r.json()
    return [item["key"] for item in data.get("items", [])]


@st.cache_data(show_spinner=True)
def cons_range_api(base: str, key: str, start: str, end: str) -> pd.DataFrame:
    if not key:
        return pd.DataFrame()
    url = f"{base}/api/v1/consumption/range"
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
        df.rename(columns={"timestamp": "datetime", "value": "consumption_kwh"})
        .set_index("datetime")
        .sort_index()
    )


# --- CSV Client ---
@st.cache_data(show_spinner=False)
def load_cons_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    return df[["datetime", "consumption_kwh"]].set_index("datetime").sort_index()


def clamp_range_to_index(
    df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp
) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Clamp selected range to df.index boundaries (prevents empty selections)."""
    if df is None or df.empty or not isinstance(df.index, pd.DatetimeIndex):
        return start, end
    min_dt = df.index.min()
    max_dt = df.index.max()
    start = max(start, min_dt)
    end = min(end, max_dt)
    if end < start:
        start = min_dt
        end = min(min_dt + pd.Timedelta(days=7), max_dt)
    return start, end


# --- UI ---
use_api = st.toggle("Use FastAPI endpoints (Default)", value=True)
api_base = st.text_input("API base", value="http://localhost:8000", disabled=not use_api)

cons_df_full: pd.DataFrame | None = None

if use_api:
    try:
        series = cons_catalog_api(api_base)
        if not series:
            st.error("Catalog empty")
            st.stop()

        if "cons_key" not in st.session_state:
            st.session_state.cons_key = series[0]

        idx = series.index(st.session_state.cons_key) if st.session_state.cons_key in series else 0
        st.session_state.cons_key = st.selectbox(
            "Select Consumption Series (API)", series, index=idx
        )

        # Default date range depends on selected series year
        y = infer_year_from_key(st.session_state.cons_key) or 2025
        d_start = pd.Timestamp(f"{y}-01-01").date()
        d_end = pd.Timestamp(f"{y}-01-07").date()

    except Exception as e:
        st.error(f"API Error: {e}")
        st.stop()

else:
    files = [str(p) for p in DEFAULTS if p.exists()]
    cons_path = st.selectbox("Consumption CSV", options=files or ["<missing>"])
    if cons_path == "<missing>":
        st.warning("No CSVs found")
        st.stop()

    cons_df_full = load_cons_csv(cons_path)
    d_start = cons_df_full.index.min().date()
    d_end = min(
        cons_df_full.index.min().date() + pd.Timedelta(days=7),
        cons_df_full.index.max().date(),
    )

left, right = st.columns(2)
with left:
    start_date = st.date_input("Start", value=d_start)
with right:
    end_date = st.date_input("End", value=d_end)

start_ts = pd.Timestamp(str(start_date), tz="UTC")
end_ts = pd.Timestamp(str(end_date), tz="UTC") + pd.Timedelta(days=1)

if use_api:
    try:
        sel = cons_range_api(
            api_base,
            st.session_state.cons_key,
            start_ts.isoformat(),
            end_ts.isoformat(),
        )
    except Exception as e:
        st.error(str(e))
        st.stop()
else:
    if cons_df_full is not None:
        sel = cons_df_full.loc[start_ts:end_ts]
    else:
        sel = pd.DataFrame()

#  If API returns empty, avoid crashes and guide user
chart, stats, preview = st.tabs(["Chart", "Stats", "Preview"])

with chart:
    if sel is None or sel.empty:
        st.warning("No data available for the selected year/date range.")
    else:
        st.line_chart(sel.rename(columns={"consumption_kwh": "kWh"}))

with stats:
    if sel is None or sel.empty or sel.shape[1] == 0:
        st.warning(
            "No data available for the selected year/date range.\n"
            "Try another year/series or adjust the dates."
        )
    else:
        st.dataframe(sel.describe())

with preview:
    if sel is None or sel.empty:
        st.info("No rows to preview for the selected range.")
    else:
        st.dataframe(sel.head(48))