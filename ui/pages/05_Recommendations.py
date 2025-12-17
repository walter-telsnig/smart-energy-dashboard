from __future__ import annotations

import requests
import pandas as pd
import streamlit as st
import altair as alt

API_BASE = "http://localhost:8000/api/v1"

st.set_page_config(page_title="Energy Recommendations", layout="wide")

st.title("⚡ Energy Usage Recommendations")
st.caption("Rule-based planning based on PV, consumption, and market prices")


with st.sidebar:
    st.header("Planning parameters")

    hours = st.slider("Planning horizon (hours)", min_value=6, max_value=168, value=24, step=6)

    price_threshold = st.slider(
        "Cheap / expensive price threshold (€/kWh)",
        min_value=0.01,
        max_value=0.50,
        value=0.12,
        step=0.01,
    )

    refresh = st.button("🔄 Generate recommendations")

if refresh:
    st.cache_data.clear()


@st.cache_data(show_spinner=False)
def load_recommendations(hours: int, price_threshold: float) -> pd.DataFrame:
    resp = requests.get(
        f"{API_BASE}/recommendations",
        params={"hours": hours, "price_threshold_eur_kwh": price_threshold},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data.get("rows", []))
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


@st.cache_data(show_spinner=False)
def load_cost_summary(hours: int, price_threshold: float) -> dict:
    resp = requests.get(
        f"{API_BASE}/recommendations/cost-summary",
        params={"hours": hours, "price_threshold_eur_kwh": price_threshold},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


@st.cache_data(show_spinner=False)
def load_timeseries_window(hours: int) -> pd.DataFrame:
    # NEW: window mode => no year needed, already normalized (pv_kwh/load_kwh/price_eur_kwh)
    resp = requests.get(
        f"{API_BASE}/timeseries/merged",
        params={"window": "true", "hours": hours},
        timeout=10,
    )
    resp.raise_for_status()
    df = pd.DataFrame(resp.json())
    if df.empty:
        return df
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    return df.sort_values("datetime").reset_index(drop=True)


try:
    reco_df = load_recommendations(hours, price_threshold)
    cost = load_cost_summary(hours, price_threshold)
    ts_df = load_timeseries_window(hours)
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()


st.subheader("💰 Cost Impact")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Baseline cost (€)", f"{cost['baseline_cost_eur']:.2f}")
kpi2.metric("Optimized cost (€)", f"{cost['optimized_cost_eur']:.2f}")
kpi3.metric("Savings (€)", f"{cost['savings_eur']:.2f}")
kpi4.metric("Savings (%)", f"{cost['savings_percent']:.2f} %")


st.subheader("📋 Recommendation Plan")
if reco_df.empty:
    st.warning("No recommendations returned.")
    st.stop()

ACTION_LABELS = {
    "charge": "🟢 Charge battery",
    "discharge": "🔴 Discharge battery",
    "shift_load": "🟡 Shift flexible load",
    "idle": "⚪ Idle",
}
reco_df["action_label"] = reco_df["action"].map(ACTION_LABELS).fillna(reco_df["action"])

st.dataframe(reco_df[["timestamp", "action_label", "reason", "score"]], use_container_width=True)


st.subheader("📈 PV, Load & Price with Recommendation Overlay")
if ts_df.empty:
    st.warning("No timeseries window returned from /timeseries/merged?window=true")
    st.stop()

plot_df = ts_df.copy()
actions = reco_df[["timestamp", "action", "score"]].rename(columns={"timestamp": "datetime"}).copy()
actions["datetime"] = pd.to_datetime(actions["datetime"], utc=True)

plot_df = plot_df.merge(actions, on="datetime", how="left")

base = alt.Chart(plot_df).encode(x=alt.X("datetime:T", title="Time"))

pv_line = base.mark_line().encode(
    y=alt.Y("pv_kwh:Q", title="Energy (kWh)"),
    tooltip=["datetime:T", "pv_kwh:Q"],
)

load_line = base.mark_line(strokeDash=[6, 3]).encode(
    y=alt.Y("load_kwh:Q"),
    tooltip=["datetime:T", "load_kwh:Q"],
)

action_points = base.transform_filter(alt.datum.action != None).mark_point(filled=True, size=80).encode(  # noqa: E711
    y=alt.Y("pv_kwh:Q"),
    shape=alt.Shape("action:N"),
    tooltip=["datetime:T", "action:N", "score:Q", "pv_kwh:Q", "load_kwh:Q", "price_eur_kwh:Q"],
)

price_line = alt.Chart(plot_df).mark_line().encode(
    x=alt.X("datetime:T", title="Time"),
    y=alt.Y("price_eur_kwh:Q", title="Price (€/kWh)"),
    tooltip=["datetime:T", "price_eur_kwh:Q"],
)

st.altair_chart((pv_line + load_line + action_points).interactive(), use_container_width=True)
st.altair_chart(price_line.interactive(), use_container_width=True)

st.caption(
    "Recommendations are overlaid as shape-coded points on the PV curve. "
    "PV and Load share the same axis; Price is shown separately."
)


with st.expander("ℹ️ How are these recommendations generated?"):
    st.markdown(
        """
**Current logic (v1):**
- Takes the latest available full-day profile from the datasets (24h)
- Projects it onto *today* (00:00 → forward, up to 1 week)
- Applies transparent rule-based decisions:
  - **Charge** when PV surplus is expected
  - **Discharge** during high-price hours
  - **Shift load** when energy is cheap and PV exists
  - **Idle** otherwise

**Cost KPIs:**
- Baseline = grid usage without any action
- Optimized = grid usage after applying recommendations
- Savings = Baseline − Optimized
"""
    )