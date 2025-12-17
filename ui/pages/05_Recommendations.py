# Streamlit UI for energy usage recommendations
# - Calls FastAPI /api/v1/recommendations
# - Shows planning from "today 00:00" forward
#
# Design notes:
#   SRP: UI only (no business logic)
#   DIP: depends on stable API contract

from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st

API_BASE = "http://localhost:8000/api/v1"

st.set_page_config(page_title="Energy Recommendations", layout="wide")

st.title("⚡ Energy Usage Recommendations")
st.caption(
    "Rule-based planning starting from today, based on PV, consumption, and market prices"
)

# ---------- controls ------------------------------------------------------------

with st.sidebar:
    st.header("Planning parameters")

    hours = st.slider(
        "Planning horizon (hours)",
        min_value=6,
        max_value=168,   # 7 days
        value=24,
        step=6,
        help="How far into the future recommendations should be generated",
    )

    price_threshold = st.slider(
        "Cheap / expensive price threshold (€/kWh)",
        min_value=0.01,
        max_value=0.50,
        value=0.12,
        step=0.01,
        help="Used to decide when discharging or shifting load makes sense",
    )

    refresh = st.button("🔄 Generate recommendations")

# ---------- info box ------------------------------------------------------------

now = datetime.now(timezone.utc)
today_str = now.strftime("%Y-%m-%d")

st.info(
    f"""
📅 **Planning window**
- Start: **{today_str} 00:00 (today)**
- Horizon: **{hours} hours**
"""
)

# ---------- data loading --------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_recommendations(hours: int, price_threshold: float) -> pd.DataFrame:
    resp = requests.get(
        f"{API_BASE}/recommendations",
        params={
            "hours": hours,
            "price_threshold_eur_kwh": price_threshold,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    df = pd.DataFrame(data["rows"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert(None)
    return df


if refresh:
    st.cache_data.clear()

try:
    df = load_recommendations(hours, price_threshold)
except Exception as e:
    st.error(f"Failed to load recommendations: {e}")
    st.stop()

# ---------- main view ------------------------------------------------------------

st.subheader("📋 Recommendation Plan")

if df.empty:
    st.warning("No recommendations returned.")
    st.stop()

# Friendly labels for actions
ACTION_LABELS = {
    "charge": "🟢 Charge battery",
    "discharge": "🔴 Discharge battery",
    "shift_load": "🟡 Shift flexible load",
    "idle": "⚪ Idle",
}

df["action_label"] = df["action"].map(ACTION_LABELS).fillna(df["action"])

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
    df.assign(hour=lambda x: x["timestamp"].dt.strftime("%m-%d %H:%M"))
      .set_index("hour")
)

st.bar_chart(chart_df["score"], height=250)

st.caption(
    "Bar height represents confidence score. "
    "Action type is shown in the table above."
)

# ---------- explanation ---------------------------------------------------------

with st.expander("ℹ️ How are these recommendations generated?"):
    st.markdown(
        """
**Current logic (v1):**

- Uses historical PV, consumption, and price data
- Starts from **today at 00:00**
- Applies a simple rule-based strategy:
  - **Charge** when PV surplus is expected
  - **Discharge** during high-price hours
  - **Shift load** when prices are low and PV is available
  - **Idle** when no clear advantage exists

This version is intentionally transparent and deterministic.

➡️ Future versions can:
- Integrate weather forecasts
- Use optimization (cost minimization)
- Add battery constraints and SoC awareness
"""
    )
