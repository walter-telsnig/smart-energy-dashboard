# ==============================================
# File: ui/app.py
# ==============================================
"""
Smart Energy Dashboard — Overview Page.
Focus: High-level status, immediate flow, and key metrics.
"""
# from ui.utils.overview_metrics import count_csv_files, count_csv_rows, total_pv_kwh
from __future__ import annotations
import streamlit as st
import requests

from streamlit_echarts import st_echarts  # type: ignore

st.set_page_config(page_title="Smart Energy Dashboard", layout="wide", page_icon="⚡")

# --- Session State (auth only) ---
if "token" not in st.session_state:
    st.session_state["token"] = None

# Gate: if not logged in, go to Landing/Login page
if not st.session_state["token"]:
    st.switch_page("pages/00_Login.py")

# --- Authenticated Dashboard ---

# 1. Sidebar Controls
with st.sidebar:
    st.header("Dashboard Settings")
    mode = st.radio("Optimization Mode", ["Economic Mode 💰", "Green Mode 🌿"],
                    help="Economic: Minimize cost. Green: Maximize self-consumption.")

    st.divider()
    if st.button("Logout"):
        st.session_state["token"] = None
        st.switch_page("pages/00_Login.py")

# 2. Header & Metrics
st.title("⚡ Energy Overview")
st.caption(f"Current Mode: **{mode}**")

# Fetch 'Live' Data (using first hour of merged series as proxy for 'now')
# In a real app, this would be `POST /api/v1/live` or similar.
metrics = {
    "pv": 0.0, "load": 0.0, "price": 0.0, "battery_soc": 50, "battery_flow": 0.0, "grid": 0.0
}

try:
    # Get 1 hour of data to simulate "live" state
    r = requests.get("http://localhost:8000/api/v1/timeseries/merged?hours=1&window=true", timeout=2)
    if r.status_code == 200:
        data = r.json()
        if data:
            row = data[0]
            metrics["pv"] = float(row.get("pv_kwh", 0))
            metrics["load"] = float(row.get("load_kwh", 0)) # type: ignore
            metrics["price"] = float(row.get("price_eur_kwh", 0))
            # Mock battery state since backend doesn't have live state persistence yet
            metrics["battery_flow"] = metrics["pv"] * 0.2 if mode == "Green Mode 🌿" else 0
except Exception:
    pass

# Calculations
pv = metrics["pv"]
load = metrics["load"]
grid_flow = load - pv + metrics["battery_flow"] # Simplified balance
self_sufficiency = min(pv, load) / load * 100 if load > 0 else 100.0
net_cost = grid_flow * metrics["price"]

# Render Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Self-Sufficiency", f"{self_sufficiency:.1f} %", delta=f"{pv:.1f} kWh PV")
with col2:
    bat_delta = f"{'+' if metrics['battery_flow'] > 0 else ''}{metrics['battery_flow']:.1f} kW"
    st.metric("Battery Status", f"{metrics['battery_soc']} %", delta=bat_delta)
with col3:
    color = "inverse" if net_cost > 0 else "normal" # inverse: red if cost > 0
    st.metric("Live Net Cost", f"{net_cost:.2f} €", delta="Spending" if net_cost > 0 else "Earning", delta_color=color)  # type: ignore

# 3. Energy Flow Visualization (Sankey)
st.subheader("Energy Flow")

# Construct Sankey Data
# Nodes: PV, Grid, Battery, House
# Links: PV->House, PV->Battery, PV->Grid, Grid->House, Battery->House
nodes = [
    {"name": "PV ☀️"},
    {"name": "Grid 🔌"},
    {"name": "Battery 🔋"},
    {"name": "House 🏠"}
]

links = []
# Very simple flow logic for demo
if pv >= load:
    # PV covers load, excess to battery/grid
    links.append({"source": "PV ☀️", "target": "House 🏠", "value": round(load, 2)})
    surplus = pv - load
    if metrics["battery_flow"] > 0: # Charging
        links.append({"source": "PV ☀️", "target": "Battery 🔋", "value": round(metrics["battery_flow"], 2)})
        surplus -= metrics["battery_flow"]
    if surplus > 0:
        links.append({"source": "PV ☀️", "target": "Grid 🔌", "value": round(surplus, 2)})
else:
    # PV insufficient
    links.append({"source": "PV ☀️", "target": "House 🏠", "value": round(pv, 2)})
    deficit = load - pv
    # Check battery discharge
    if metrics["battery_flow"] < 0: # Discharging
        discharge = abs(metrics["battery_flow"])
        links.append({"source": "Battery 🔋", "target": "House 🏠", "value": round(discharge, 2)})
        deficit -= discharge
    if deficit > 0:
        links.append({"source": "Grid 🔌", "target": "House 🏠", "value": round(deficit, 2)})

option = {
    "tooltip": {"trigger": "item", "triggerOn": "mousemove"},
    "series": [
        {
            "type": "sankey",
            "data": nodes,
            "links": links,
            "emphasis": {"focus": "adjacency"},
            "lineStyle": {"color": "gradient", "curveness": 0.5},
            "label": {"position": "top"},
            "levels": [
                {
                    "depth": 0,
                    "itemStyle": {"color": "#fbb4ae"},
                    "lineStyle": {"color": "source", "opacity": 0.6},
                },
                {
                    "depth": 1,
                    "itemStyle": {"color": "#b3cde3"},
                    "lineStyle": {"color": "source", "opacity": 0.6},
                },
                {
                    "depth": 2,
                    "itemStyle": {"color": "#ccebc5"},
                    "lineStyle": {"color": "source", "opacity": 0.6},
                },
                {
                    "depth": 3,
                    "itemStyle": {"color": "#decbe4"},
                    "lineStyle": {"color": "source", "opacity": 0.6},
                },
            ],
        }
    ],
}

st_echarts(options=option, height="500px")
st.info("Use the sidebar: PV • Prices • Consumption • Compare • Battery Sim")

#--------------------------------------------------------------
# added a new overview section: high-level dataset availability
#--------------------------------------------------------------
st.markdown("---")
st.subheader("Overview")

metric_cols = st.columns(3)

def count_csv_files(folder: Path) -> int:
    """
    Count number of CSV files in a given folder.
    This is intentionally simple; can b extended later
    to compute energy KPIs from the same folders.
    """
    if not folder.exists():
        return 0
    return len(list(folder.glob("*.csv")))
    
def count_csv_rows(folder: Path) -> int:
    
    #count total number of rows across all CSV files in a folder.

    if not folder.exists():
        return 0

    total = 0
    for csv_file in folder.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            total += len(df)
        except Exception:
            #if csv is unreadable, skip it instead of breaking the dashboard
            continue
    return total

def total_pv_kwh(folder: Path) -> float:
    #sum PV energy (kwh) across all CSV files in the given folder.
    #if a file has 'production_kwh', we use it diirectly
    # if it has 'production_kw', we assume hourly data and convert to kwh

    if not folder.exists():
        return 0.0

    total_kwh = 0.0
    
    for csv_file in folder.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
        except Exception:
            continue
        
        #decide which column holds the PV production
        if "production_kwh" in df.columns:
            values = pd.to_numeric(df["production_kwh"], errors="coerce")
        elif "production_kw" in df.columns:
            #hourly data: KW*1h = kwh

            values = pd.to_numeric(df["production_kw"], errors="coerce") * 1.0
        else:
            #unknown schema, skip this file
            continue
        total_kwh += float(values.sum())

    return total_kwh


 #----dataset counts---------------------------
with metric_cols[0]:
    st.metric(
        label="PV datasets (CSV)",
        value=count_csv_files(paths["PV"]),
        help="Number of PV CSV files found in infra/data/pv",
    )

with metric_cols[1]:
    st.metric(
        label="Market price datasets (CSV)",
        value=count_csv_files(paths["Market"]),
        help="Number of market price CSV files found in infra/data/market",
    )

with metric_cols[2]:
    st.metric(
        label="Consumption datasets (CSV)",
        value=count_csv_files(paths["Consumption"]),
        help="Number of consumption CSV files found in infra/data/consumption",
    )
#-------row counts -----------------------------
rows_cols = st.columns(3)

with rows_cols[0]:
    st.metric(
        label="PV time series points (rows)",
        value=count_csv_rows(paths["PV"]),
        help="Total number of rows across all PV CSV files.",
    )
with rows_cols[1]:
    st.metric(
        label="Market time series points (rows)",
        value=count_csv_rows(paths["Market"]),
        help="Total number of rows across all Market CSV files.",
    )
with rows_cols[2]:
    st.metric(
        label="Consumption time series points (rows)",
        value=count_csv_rows(paths["Consumption"]),
        help="Total number of rows across all Consumption CSV files.",
    )
#--------energy KPIs------------------------------
energy_cols = st.columns(3)

with energy_cols[0]:
    st.metric(
        label="Total PV energy (kwh)",
        value=f"{total_pv_kwh(paths['PV']):,.0f}",
        help="Sum of PV energy across all PV CSV files.",
    )