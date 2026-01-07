from __future__ import annotations

import requests
import pandas as pd
import streamlit as st
import altair as alt
from utils.theme import apply_global_style, sidebar_nav
from utils.auth import auth_headers


st.set_page_config(
    layout="wide", page_title="Recommendations • Smart Energy Dashboard", page_icon="✅"
)

apply_global_style()
sidebar_nav(active="Recommendations")

if "token" not in st.session_state or not st.session_state["token"]:
    st.switch_page("pages/00_Login.py")


def _auth_headers() -> dict:
    tok = st.session_state.get("token")
    return {"Authorization": f"Bearer {tok}"} if tok else {}


API_BASE = "http://localhost:8000/api/v1"

if "token" not in st.session_state or st.session_state["token"] is None:
    st.warning("Please log in to access this page.")
    st.stop()

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("Planning")

    hours = st.slider(
        "Planning horizon (hours)", min_value=6, max_value=168, value=24, step=6
    )
    battery_enabled = st.toggle("Use battery recommendations", value=True)
    refresh = st.button("Generate recommendations")

if refresh:
    st.cache_data.clear()


def _bool_param(v: bool) -> str:
    return "true" if v else "false"


# ---------------- API loaders ----------------
@st.cache_data(show_spinner=False)
def load_recommendations(hours: int, battery_enabled: bool) -> pd.DataFrame:
    params: dict[str, str] = {
        "hours": str(int(hours)),
        "battery_enabled": _bool_param(battery_enabled),
    }
    resp = requests.get(
        f"{API_BASE}/recommendations", params=params, timeout=10, headers=auth_headers()
    )
    resp.raise_for_status()

    data = resp.json()
    df = pd.DataFrame(data.get("rows", []))
    if df.empty:
        return df

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


@st.cache_data(show_spinner=False)
def load_cost_summary(hours: int, battery_enabled: bool) -> dict:
    params: dict[str, str] = {
        "hours": str(int(hours)),
        "battery_enabled": _bool_param(battery_enabled),
    }
    resp = requests.get(
        f"{API_BASE}/recommendations/cost-summary",
        params=params,
        timeout=10,
        headers=auth_headers(),
    )
    resp.raise_for_status()
    return resp.json()


@st.cache_data(show_spinner=False)
def load_timeseries_window(hours: int) -> pd.DataFrame:
    params: dict[str, str] = {
        "window": "true",
        "hours": str(int(hours)),
    }
    resp = requests.get(
        f"{API_BASE}/timeseries/merged",
        params=params,
        timeout=10,
        headers=auth_headers(),
    )
    resp.raise_for_status()

    df = pd.DataFrame(resp.json())
    if df.empty:
        return df

    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    return df.sort_values("datetime").reset_index(drop=True)


# ---------------- Load data ----------------
try:
    reco_df = load_recommendations(hours, battery_enabled)
    cost = load_cost_summary(hours, battery_enabled)
    ts_df = load_timeseries_window(hours)
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()


# ---------------- Header + Current Weather ----------------
left, right = st.columns([3, 1])

with left:
    st.title("⚡ Energy Usage Recommendations")
    st.caption(
        "Simple, human-friendly suggestions based on PV, consumption, prices, and weather"
    )

with right:
    # push weather down a bit so it doesn't collide with the top white ribbon
    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    if (
        not ts_df.empty
        and "temp_c" in ts_df.columns
        and "cloud_cover_pct" in ts_df.columns
    ):
        now = (pd.Timestamp.utcnow() + pd.Timedelta(hours=1)).floor("h")
        current_slice = ts_df[ts_df["datetime"] <= now]
        current_row = ts_df.iloc[0] if current_slice.empty else current_slice.iloc[-1]

        temp = current_row.get("temp_c", None)
        cloud = current_row.get("cloud_cover_pct", None)

        cloud_icon = "☁️"
        if cloud is not None:
            try:
                c = float(cloud)
                if c < 25:
                    cloud_icon = "☀️"
                elif c < 70:
                    cloud_icon = "⛅"
                else:
                    cloud_icon = "☁️"
            except Exception:
                pass

        if temp is not None and cloud is not None:
            st.markdown(f"### {cloud_icon} {float(temp):.1f}°C")
            st.caption(f"Cloud cover: {float(cloud):.0f}%")
        else:
            st.caption("Weather: n/a")
    else:
        st.caption("Weather: n/a")


# ---------------- Highlight: current-hour suggestion ----------------
if reco_df.empty:
    st.warning("No recommendations returned.")
    st.stop()

now = (pd.Timestamp.utcnow() + pd.Timedelta(hours=1)).floor("h")
reco_df = reco_df.sort_values("timestamp").reset_index(drop=True)

future = reco_df[reco_df["timestamp"] >= now]
current_rec = future.iloc[0] if not future.empty else reco_df.iloc[-1]

ACTION_LABELS = {
    "charge": "🟢 Store solar energy (charge the battery)",
    "discharge": "🔴 Use battery now (avoid grid usage)",
    "shift_load": "🟡 Good time to run appliances (dishwasher / laundry / charging)",
    "idle": "⚪ No action needed",
}

current_action_label = ACTION_LABELS.get(
    str(current_rec.get("action", "")), str(current_rec.get("action", ""))
)
current_reason = str(current_rec.get("reason", "")).strip()
current_time_str = pd.to_datetime(current_rec["timestamp"], utc=True).strftime("%H:%M")

st.info(
    f"**Right now ({current_time_str}) → {current_action_label}**  \n{current_reason}"
)


# ---------------- KPIs ----------------
st.subheader("💰 Cost Impact")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

baseline = float(cost.get("baseline_cost_eur", 0.0))
optimized = float(cost.get("optimized_cost_eur", 0.0))
savings = float(cost.get("savings_eur", 0.0))

savings_pct = (savings / baseline) * 100 if baseline > 0 else 0.0

kpi1.metric("Baseline cost (€)", f"{baseline:.2f}")
kpi2.metric("Optimized cost (€)", f"{optimized:.2f}")
kpi3.metric("Savings (€)", f"{savings:.2f}")
kpi4.metric("Savings (%)", f"{savings_pct:.2f} %")


# ---------------- Recommendations Table ----------------
st.subheader("📋 Recommendation Plan")

reco_df["action_label"] = reco_df["action"].map(ACTION_LABELS).fillna(reco_df["action"])
st.dataframe(
    reco_df[["timestamp", "action_label", "reason", "score"]], use_container_width=True
)


# ---------------- PV / Load / Price with overlay ----------------
st.subheader("📈 PV, Load & Price (with recommendations)")

if ts_df.empty:
    st.warning("No timeseries returned from /timeseries/merged")
    st.stop()

plot_df = ts_df.copy()

actions = (
    reco_df[["timestamp", "action", "score"]]
    .rename(columns={"timestamp": "datetime"})
    .copy()
)
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

action_points = (
    base.transform_filter(alt.datum.action != None)  # noqa: E711
    .mark_point(filled=True, size=80)
    .encode(
        y=alt.Y("pv_kwh:Q"),
        shape=alt.Shape("action:N"),
        tooltip=[
            "datetime:T",
            "action:N",
            "score:Q",
            "pv_kwh:Q",
            "load_kwh:Q",
            "price_eur_kwh:Q",
        ],
    )
)

price_line = (
    alt.Chart(plot_df)
    .mark_line()
    .encode(
        x=alt.X("datetime:T", title="Time"),
        y=alt.Y("price_eur_kwh:Q", title="Price (€/kWh)"),
        tooltip=["datetime:T", "price_eur_kwh:Q"],
    )
)

st.altair_chart(
    (pv_line + load_line + action_points).interactive(), use_container_width=True
)
st.altair_chart(price_line.interactive(), use_container_width=True)

with st.expander("ℹ️ What does this mean?"):
    st.markdown(
        """
**Battery ON**
- The plan tries to store extra solar energy during the day and use it later, so you buy less electricity from the grid.

**Battery OFF**
- You will still see advice like “run appliances when solar is high”, but no battery charging/discharging actions.

**Shift load**
- Means: move flexible tasks (dishwasher, laundry, charging devices) into hours where solar or price is favorable.
"""
    )
