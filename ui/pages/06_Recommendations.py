from __future__ import annotations

import requests
import pandas as pd
import streamlit as st
import altair as alt

API_BASE = "http://localhost:8000/api/v1"

st.set_page_config(page_title="Energy Recommendations", layout="wide")

# --- Title row with right-side weather KPI ---
title_col, weather_col = st.columns([3, 1], vertical_alignment="center")
with title_col:
    st.title("⚡ Energy Usage Recommendations")
    st.caption("Battery-aware planning based on PV, consumption, market prices, and weather")

with st.sidebar:
    st.header("Planning parameters")

    hours = st.slider("Planning horizon (hours)", min_value=6, max_value=168, value=24, step=6)

    battery_enabled = st.toggle("Battery enabled", value=True)

    auto_threshold = st.checkbox("Auto price threshold", value=True, help="Auto = 75th percentile of prices in the horizon")

    with st.expander("Advanced settings"):
        # Only used if auto_threshold = False
        price_threshold = st.slider(
            "Manual price threshold (€/kWh)",
            min_value=0.01,
            max_value=0.50,
            value=0.12,
            step=0.01,
            disabled=auto_threshold,
        )

        st.markdown("**Battery defaults (home typical)**")
        capacity_kwh = st.slider("Capacity (kWh)", 1.0, 30.0, 10.0, 0.5)
        p_charge_max_kw = st.slider("Max charge power (kW)", 0.5, 15.0, 5.0, 0.5)
        p_discharge_max_kw = st.slider("Max discharge power (kW)", 0.5, 15.0, 5.0, 0.5)
        efficiency = st.slider("Efficiency (η)", 0.70, 0.99, 0.92, 0.01)
        initial_soc_kwh = st.slider("Initial SoC (kWh)", 0.0, float(capacity_kwh), float(min(5.0, capacity_kwh)), 0.5)

        soc_min = st.slider("SoC min (fraction)", 0.0, 0.5, 0.10, 0.01)
        soc_max = st.slider("SoC max (fraction)", 0.5, 1.0, 0.95, 0.01)

        export_mode = st.selectbox("Export revenue mode", ["feed_in", "market"], index=0)
        feed_in_tariff = st.number_input("Feed-in tariff (€/kWh)", min_value=0.0, value=0.08, step=0.01)

    refresh = st.button("🔄 Generate recommendations")

if refresh:
    st.cache_data.clear()


@st.cache_data(show_spinner=False)
def load_recommendations() -> pd.DataFrame:
    params = {
        "hours": hours,
        "battery_enabled": str(battery_enabled).lower(),
        "capacity_kwh": capacity_kwh,
        "soc_min": soc_min,
        "soc_max": soc_max,
        "eta_c": efficiency,
        "eta_d": efficiency,
        "p_charge_max_kw": p_charge_max_kw,
        "p_discharge_max_kw": p_discharge_max_kw,
        "initial_soc_kwh": initial_soc_kwh,
    }
    if not auto_threshold:
        params["price_threshold_eur_kwh"] = price_threshold  # manual

    resp = requests.get(f"{API_BASE}/recommendations", params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data.get("rows", []))
    if df.empty:
        return df
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


@st.cache_data(show_spinner=False)
def load_cost_summary() -> dict:
    params = {
        "hours": hours,
        "battery_enabled": str(battery_enabled).lower(),
        "capacity_kwh": capacity_kwh,
        "soc_min": soc_min,
        "soc_max": soc_max,
        "eta_c": efficiency,
        "eta_d": efficiency,
        "p_charge_max_kw": p_charge_max_kw,
        "p_discharge_max_kw": p_discharge_max_kw,
        "initial_soc_kwh": initial_soc_kwh,
        "export_mode": export_mode,
        "feed_in_tariff_eur_per_kwh": feed_in_tariff,
    }
    if not auto_threshold:
        params["price_threshold_eur_kwh"] = price_threshold

    resp = requests.get(f"{API_BASE}/recommendations/cost-summary", params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


@st.cache_data(show_spinner=False)
def load_timeseries_window() -> pd.DataFrame:
    resp = requests.get(f"{API_BASE}/timeseries/merged", params={"window": "true", "hours": hours}, timeout=20)
    resp.raise_for_status()
    df = pd.DataFrame(resp.json())
    if df.empty:
        return df
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    return df.sort_values("datetime").reset_index(drop=True)


try:
    reco_df = load_recommendations()
    cost = load_cost_summary()
    ts_df = load_timeseries_window()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()


# --- Weather KPI (top-right) ---
def _weather_icon(temp_c: float | None, cloud: float | None) -> str:
    if cloud is None:
        return "🌡️"
    if cloud >= 80:
        return "☁️"
    if cloud >= 40:
        return "⛅"
    return "☀️"


if not ts_df.empty:
    now_row = ts_df.iloc[0]  # planning starts at today 00:00 UTC
    temp = None if pd.isna(now_row.get("temp_c")) else float(now_row.get("temp_c"))
    cloud = None if pd.isna(now_row.get("cloud_cover_pct")) else float(now_row.get("cloud_cover_pct"))
    icon = _weather_icon(temp, cloud)

    with weather_col:
        st.markdown("#### Weather now")
        if temp is not None:
            st.metric(f"{icon} Temp", f"{temp:.1f} °C")
        else:
            st.metric(f"{icon} Temp", "—")
        if cloud is not None:
            st.metric("☁️ Cloud", f"{cloud:.0f} %")
        else:
            st.metric("☁️ Cloud", "—")


# --- KPIs ---
st.subheader("💰 Cost Impact")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Baseline cost (€)", f"{cost['baseline_cost_eur']:.2f}")
kpi2.metric("Optimized cost (€)", f"{cost['optimized_cost_eur']:.2f}")
kpi3.metric("Savings (€)", f"{cost['savings_eur']:.2f}")
kpi4.metric("Savings (%)", f"{cost['savings_percent']:.2f} %")

st.caption(
    "Baseline = no battery. Optimized = battery simulation (SoC + power limits + efficiency). "
    "Export revenue uses feed-in tariff by default."
)

# --- Recommendation plan ---
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

# --- PV/Load overlay chart (keep it) + price chart (keep it) ---
st.subheader("📈 PV, Load & Price with Recommendation Overlay")

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

with st.expander("ℹ️ What does 'Auto price threshold' do?"):
    st.markdown(
        """
- The **price threshold** is only used to decide when to show the **“Shift flexible load”** advice (dishwasher, washing machine).
- With **Auto threshold**, we compute a threshold from the chosen horizon:
  - **threshold = 75th percentile of prices**
- You can switch Auto off and set a manual threshold in **Advanced settings**.
"""
    )
