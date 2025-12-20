# ==============================================
# File: ui/pages/03_Consumption.py
# ==============================================
"""
Consumption page: View household load from CSV.
- Tabs: Chart | Stats | Preview
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(layout="wide")
st.title("🏠 Household Consumption - CSV Version")

DATA_DIR = Path("infra/data/consumption")
DEFAULTS = [
    DATA_DIR / "consumption_2025_hourly.csv",
    DATA_DIR / "consumption_2026_hourly.csv",
    DATA_DIR / "consumption_2027_hourly.csv",
]

@st.cache_data(show_spinner=False)
def load_cons(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    return df[["datetime", "consumption_kwh"]].set_index("datetime").sort_index()

files = [str(p) for p in DEFAULTS if p.exists()]
cons_path = st.selectbox("Consumption CSV", options=files or ["<missing>"])
if cons_path == "<missing>":
    st.warning("No consumption CSVs found in infra/data/consumption")
    st.stop()

cons = load_cons(cons_path)

left, right = st.columns(2)
with left:
    start = st.date_input("Start", value=cons.index.min().date())
with right:
    end = st.date_input("End", value=min(cons.index.min().date() + pd.Timedelta(days=7), cons.index.max().date()))

start_ts = pd.Timestamp(start, tz="UTC")
end_ts = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
sel = cons.loc[start_ts:end_ts]

chart, stats, preview = st.tabs(["Chart", "Stats", "Preview"])
with chart:
    st.line_chart(sel.rename(columns={"consumption_kwh": "Consumption (kWh)"}))
with stats:
    st.dataframe(sel.describe())
with preview:
    st.dataframe(sel.head(48))

