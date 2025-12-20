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
from pathlib import Path

st.set_page_config(layout="wide")
import importlib.util
from pathlib import Path

def _load_auth():
    auth_path = Path(__file__).resolve().parents[1] / "auth.py"  # ui/auth.py
    spec = importlib.util.spec_from_file_location("auth", auth_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load auth module from {auth_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

auth = _load_auth()
auth.require_login()
auth.logout_button()

st.title("💶 Electricity Prices (EPEX AT)")

DATA_DIR = Path("infra/data/market")
DEFAULTS = [
    DATA_DIR / "price_2025_hourly.csv",
    DATA_DIR / "price_2026_hourly.csv",
    DATA_DIR / "price_2027_hourly.csv",
]

@st.cache_data(show_spinner=False)
def load_price(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    return df[["datetime", "price_eur_mwh"]].set_index("datetime").sort_index()

files = [str(p) for p in DEFAULTS if p.exists()]
price_path = st.selectbox("Price CSV", options=files or ["<missing>"])
if price_path == "<missing>":
    st.warning("No price CSVs found in infra/data/market")
    st.stop()

price = load_price(price_path)

left, right = st.columns(2)
with left:
    start = st.date_input("Start", value=price.index.min().date())
with right:
    end = st.date_input("End", value=min(price.index.min().date() + pd.Timedelta(days=7), price.index.max().date()))

start_ts = pd.Timestamp(start, tz="UTC")
end_ts = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)
sel = price.loc[start_ts:end_ts]

chart, stats, preview = st.tabs(["Chart", "Stats", "Preview"])
with chart:
    st.line_chart(sel.rename(columns={"price_eur_mwh": "€/MWh"}))
with stats:
    st.dataframe(sel.describe())
with preview:
    st.dataframe(sel.head(48))