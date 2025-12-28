# ==============================================
# File: ui/pages/99_Battery_Sim.py
# ==============================================
"""
Battery Simulation page (server-wired):
- Calls FastAPI for both simulation and cost summary.
- Inputs: date range, CSV paths (PV + consumption + prices), battery params.
- Tabs: SoC | Grid Flows | Costs (from /cost-summary) | Table

Endpoints used:
- POST /api/v1/battery/simulate
- POST /api/v1/battery/cost-summary
"""
from __future__ import annotations
import streamlit as st
import pandas as pd
import requests
import streamlit as st
from utils.theme import apply_global_style, sidebar_nav

st.set_page_config(layout="wide", page_title="Battery Sim • Smart Energy Dashboard", page_icon="🔋")

apply_global_style()
sidebar_nav(active="Battery Sim")

if "token" not in st.session_state or not st.session_state["token"]:
    st.switch_page("pages/00_Login.py")

def _auth_headers() -> dict:
    tok = st.session_state.get("token")
    return {"Authorization": f"Bearer {tok}"} if tok else {}


if "token" not in st.session_state or st.session_state["token"] is None:
    st.warning("Please log in to access this page.")
    st.stop()
st.title("🔋 Battery Simulation")

api_base = st.text_input("API base", value="http://localhost:8000")

# Inputs
left, right = st.columns(2)
with left:
    start = st.text_input("Start (ISO)", value="2025-01-01T00:00:00Z")
with right:
    end = st.text_input("End (ISO)", value="2025-01-07T00:00:00Z")

st.subheader("Battery Parameters")
cols = st.columns(3)
with cols[0]:
    capacity_kwh = st.number_input("Capacity (kWh)", 1.0, 100.0, 10.0, 0.5)
    soc_min = st.slider("SOC min", 0.0, 0.5, 0.05, 0.01)
    soc_max = st.slider("SOC max", 0.5, 1.0, 0.95, 0.01)
with cols[1]:
    eta_c = st.slider("η charge", 0.6, 1.0, 0.95, 0.01)
    eta_d = st.slider("η discharge", 0.6, 1.0, 0.95, 0.01)
with cols[2]:
    p_charge = st.number_input("P charge max (kW)", 0.5, 20.0, 5.0, 0.5)
    p_discharge = st.number_input("P discharge max (kW)", 0.5, 20.0, 5.0, 0.5)

st.subheader("Data paths (CSV)")
PV_DEFAULT = "infra/data/pv/pv_2025_hourly.csv"
CONS_DEFAULT = "infra/data/consumption/consumption_2025_hourly.csv"
PRICE_DEFAULT = "infra/data/market/price_2025_hourly.csv"
pv_csv = st.text_input("PV CSV", value=PV_DEFAULT)
cons_csv = st.text_input("Consumption CSV", value=CONS_DEFAULT)
price_csv = st.text_input("Price CSV", value=PRICE_DEFAULT)

st.subheader("Pricing")
price_export_market = st.checkbox("Use market price for export", value=False)
feed_in_tariff_eur_per_kwh = st.number_input(
    "Feed-in tariff (€/kWh)", min_value=0.0, value=0.08, step=0.01, format="%.3f",
    help="Used when market export is disabled"
)

if st.button("Simulate (server)", type="primary"):
    try:
        sim_payload = {
            "start": start,
            "end": end,
            "params": {
                "capacity_kwh": capacity_kwh,
                "soc_min": soc_min,
                "soc_max": soc_max,
                "eta_c": eta_c,
                "eta_d": eta_d,
                "p_charge_max_kw": p_charge,
                "p_discharge_max_kw": p_discharge,
            },
            "pv_csv": pv_csv,
            "consumption_csv": cons_csv,
        }
        # 1) Simulation series for charts
        r_sim = requests.post(f"{api_base}/api/v1/battery/simulate", json=sim_payload, timeout=90)
        r_sim.raise_for_status()
        sim_points = r_sim.json()["points"]
        sim = pd.DataFrame(sim_points)
        sim["datetime"] = pd.to_datetime(sim["datetime"], utc=True)
        sim = sim.set_index("datetime").sort_index()

        # 2) Cost summary (server-side pricing)
        cost_payload = {
            **sim_payload,
            "price_csv": price_csv,
            "export_mode": "market" if price_export_market else "feed_in",
            "feed_in_tariff_eur_per_kwh": feed_in_tariff_eur_per_kwh,
        }
        r_cost = requests.post(f"{api_base}/api/v1/battery/cost-summary", json=cost_payload, timeout=90)
        r_cost.raise_for_status()
        cost = r_cost.json()
        daily = pd.DataFrame(cost.get("daily_breakdown", []))
        if not daily.empty:
            daily["datetime"] = pd.to_datetime(daily["datetime"], utc=True)
            daily = daily.set_index("datetime").sort_index()

        soc_tab, flows_tab, cost_tab, table_tab = st.tabs(["SoC", "Grid Flows", "Costs (server)", "Table"]) 
        with soc_tab:
            st.line_chart(sim[["soc_kwh"]])
        with flows_tab:
            st.line_chart(sim[["grid_import_kwh", "grid_export_kwh", "charge_kwh", "discharge_kwh"]])
        with cost_tab:
            k1, k2, k3 = st.columns(3)
            k1.metric("Import cost (EUR)", f"{cost['total_import_cost_eur']:.2f}")
            k2.metric("Export revenue (EUR)", f"{cost['total_export_revenue_eur']:.2f}")
            k3.metric("Net cost (EUR)", f"{cost['total_net_cost_eur']:.2f}")
            if not daily.empty:
                st.bar_chart(daily[["import_cost_eur", "export_revenue_eur", "net_cost_eur"]])
        with table_tab:
            st.dataframe(sim.head(48))

        st.success("Simulation completed")
    except Exception as e:
        st.error(f"Simulation failed: {e}")