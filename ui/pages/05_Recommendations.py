# Streamlit UI for energy usage recommendations
# - Calls FastAPI /api/v1/recommendations
# - Visualizes actions and explains reasoning
# Design notes:
#   SRP: UI only (no business logic)
#   DIP: depends on stable API contract

import requests
import pandas as pd
import streamlit as st

API_BASE = "http://localhost:8000/api/v1"

st.set_page_config(page_title="Energy Recommendations", layout="wide")

st.title("⚡ Energy Usage Recommendations")
st.caption("Rule-based planning based on PV, consumption, and market prices")

# ---------- controls ------------------------------------------------------------

with st.sidebar:
    st.header("Planning parameters")

    year = st.selectbox("Dataset year", [2025, 2026, 2027], index=2)
    hours = st.slider("Planning horizon (hours)", min_value=6, max_value=168, value=24, step=6)
    price_threshold = st.slider(
        "Cheap / expensive price threshold (€/kWh)",
        min_value=0.01,
        max_value=0.50,
        value=0.12,
        step=0.01,
    )

    refresh = st.button(" Generate recommendations")

# ---------- data loading --------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_recommendations(year: int, hours: int, price_threshold: float) -> pd.DataFrame:
    resp = requests.get(
        f"{API_BASE}/recommendations",
        params={
            "year": year,
            "hours": hours,
            "price_threshold_eur_kwh": price_threshold,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data["rows"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


if refresh:
    st.cache_data.clear()

try:
    df = load_recommendations(year, hours, price_threshold)
except Exception as e:
    st.error(f"Failed to load recommendations: {e}")
    st.stop()

# ---------- main view ------------------------------------------------------------

st.subheader("📋 Recommendation Plan")

if df.empty:
    st.warning("No recommendations returned.")
    st.stop()

# Color coding for actions
ACTION_COLORS = {
    "charge": "🟢 Charge battery",
    "discharge": "🔴 Discharge battery",
    "shift_load": "🟡 Shift flexible load",
    "idle": "⚪ Idle",
}

df["action_label"] = df["action"].map(ACTION_COLORS).fillna(df["action"])

st.dataframe(
    df[["timestamp", "action_label", "reason", "score"]],
    use_container_width=True,
)

# ---------- KPIs ----------------------------------------------------------------

st.subheader("📊 Summary")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Charge hours", int((df["action"] == "charge").sum()))
col2.metric("Discharge hours", int((df["action"] == "discharge").sum()))
col3.metric("Load shifts", int((df["action"] == "shift_load").sum()))
col4.metric("Idle hours", int((df["action"] == "idle").sum()))

# ---------- charts --------------------------------------------------------------

st.subheader("📈 Action Timeline")

chart_df = (
    df.assign(hour=lambda x: x["timestamp"].dt.strftime("%Y-%m-%d %H:%M"))
      .set_index("hour")
)

st.bar_chart(
    chart_df["score"],
    height=250,
)

st.caption(
    "Bar height represents confidence score. "
    "Action type is shown in the table above."
)

# ---------- explanation ---------------------------------------------------------

with st.expander(" How are these recommendations generated?"):
    st.markdown(
        """
**Current logic (v1):**
- Uses the last 24h PV / consumption / price pattern
- Projects it into the future (baseline repetition)
- Applies simple rules:
  - **Charge** when PV surplus is expected
  - **Discharge** during high-price hours
  - **Shift load** when energy is cheap and PV exists
  - **Idle** otherwise

This is intentionally simple and transparent.
Future versions can replace this logic with optimization or ML.
"""
    )
