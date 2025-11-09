# ui/pages/04_Compare.py
"""
Compare page: Overlay PV, Consumption, and Prices; compute basic KPIs.
- Tabs: Overlay | Normalized Overlay | Correlations | Preview
- Robust CSV loader that auto-detects likely value columns; converts PV kW→kWh if needed.
"""

from __future__ import annotations
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(layout="wide")
st.title("📊 Compare — PV vs. Consumption vs. Prices")

PV_PATH = Path("infra/data/pv/pv_2025_hourly.csv")
CONS_PATH = Path("infra/data/consumption/consumption_2025_hourly.csv")
PRICE_PATH = Path("infra/data/market/price_2025_hourly.csv")

# Acceptable column aliases per data type
ALIASES = {
    "pv": ["production_kwh", "production_kw", "pv_kwh", "pv_kw", "pv", "value", "generation_kwh", "generation_kw", "production"],
    "cons": ["consumption_kwh", "load_kwh", "consumption", "load", "value"],
    "price": ["price_eur_mwh", "eur_mwh", "price", "value"],
}

def _pick_col(df: pd.DataFrame, candidates: list[str]) -> str:
    lower_cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand in lower_cols:
            return lower_cols[cand]
    for cand in candidates:
        if cand in df.columns:
            return cand
    return ""  # none found

@st.cache_data(show_spinner=False)
def load_any(path: str | Path, kind: str) -> pd.DataFrame:
    """
    kind: 'pv' | 'cons' | 'price'
    Returns DataFrame indexed by datetime with a single canonical column:
      - pv    -> 'production_kwh' (auto-converts from kW if needed)
      - cons  -> 'consumption_kwh'
      - price -> 'price_eur_mwh'
    """
    path = str(path)
    df = pd.read_csv(path)

    # Time column
    if "datetime" not in df.columns:
        if "timestamp" in df.columns:
            df = df.rename(columns={"timestamp": "datetime"})
        else:
            raise KeyError(
                f"CSV '{path}' must contain a 'datetime' column (UTC). "
                f"Available columns: {list(df.columns)}"
            )

    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)

    # Detect value column
    col = _pick_col(df, ALIASES[kind])
    if not col:
        raise KeyError(
            f"Could not find a suitable value column for kind='{kind}' in '{path}'.\n"
            f"Expected one of {ALIASES[kind]} (case-insensitive). "
            f"Available columns: {list(df.columns)}"
        )

    # Canonical target name
    target_name = {
        "pv": "production_kwh",
        "cons": "consumption_kwh",
        "price": "price_eur_mwh",
    }[kind]

    out = (
        df[["datetime", col]]
        .rename(columns={col: target_name})
        .set_index("datetime")
        .sort_index()
    )

    # Convert PV power (kW) → energy (kWh) if necessary (hourly resolution assumption)
    if kind == "pv" and target_name in out.columns:
        original = col.lower()
        if original.endswith("_kw") or original in ("pv_kw",):
            # hourly step ⇒ kW * 1h = kWh
            out[target_name] = out[target_name].astype("float64") * 1.0

    return out

# --- UI controls ---
pv_path = st.text_input("PV CSV", value=str(PV_PATH))
cons_path = st.text_input("Consumption CSV", value=str(CONS_PATH))
price_path = st.text_input("Price CSV", value=str(PRICE_PATH))

# Load with helpful errors
try:
    pv = load_any(pv_path, "pv")
    cons = load_any(cons_path, "cons")
    price = load_any(price_path, "price")
except Exception as e:
    st.error(str(e))
    st.stop()

# Select common window
min_start = max(pv.index.min(), cons.index.min(), price.index.min()).date()
max_end = min(pv.index.max(), cons.index.max(), price.index.max()).date()
left, right = st.columns(2)
with left:
    start = st.date_input("Start", value=min_start, min_value=min_start, max_value=max_end)
with right:
    end = st.date_input("End", value=min(min_start + pd.Timedelta(days=7), max_end),
                        min_value=min_start, max_value=max_end)

start_ts = pd.Timestamp(start, tz="UTC")
end_ts = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)

j = (
    pv.loc[start_ts:end_ts]
      .join(cons.loc[start_ts:end_ts], how="inner")
      .join(price.loc[start_ts:end_ts], how="inner")
)

overlay, norm, corr, preview = st.tabs(["Overlay", "Normalized", "Correlations", "Preview"]) 
with overlay:
    st.line_chart(j.rename(columns={
        "production_kwh": "PV (kWh)",
        "consumption_kwh": "Consumption (kWh)",
        "price_eur_mwh": "Price (€/MWh)"
    }))

with norm:
    jj = j.copy()
    for c in jj.columns:
        v = jj[c]
        jj[c] = (v - v.min()) / (v.max() - v.min() + 1e-9)
    st.line_chart(jj.rename(columns={
        "production_kwh": "PV (norm)",
        "consumption_kwh": "Consumption (norm)",
        "price_eur_mwh": "Price (norm)"
    }))

with corr:
    corr_df = j.corr(numeric_only=True)
    st.dataframe(corr_df)

with preview:
    st.dataframe(j.head(48))

# KPIs
st.subheader("KPIs (selected window)")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("PV energy (kWh)", f"{j['production_kwh'].sum():.1f}")
with col2:
    st.metric("Consumption (kWh)", f"{j['consumption_kwh'].sum():.1f}")
with col3:
    sc = (j[['production_kwh','consumption_kwh']].min(axis=1)).sum() / j['production_kwh'].sum() if j['production_kwh'].sum() > 0 else 0
    st.metric("Self-consumption ratio", f"{100*sc:.1f}%")
with col4:
    st.metric("Avg price (€/MWh)", f"{j['price_eur_mwh'].mean():.1f}")
