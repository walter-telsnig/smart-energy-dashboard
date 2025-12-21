# ==============================================
# File: ui/app.py
# ==============================================
"""
Smart Energy Dashboard — Overview Page.
Focus: High-level status, immediate flow, and key metrics.
"""
from __future__ import annotations
import streamlit as st
import requests

from streamlit_echarts import st_echarts  # type: ignore

st.set_page_config(page_title="Smart Energy Dashboard", layout="wide", page_icon="⚡")

# --- Session State & Login ---
if "token" not in st.session_state:
    st.session_state["token"] = None

def login():
    st.title("🔐 Login")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In")
        
        if submitted:
            try:
                res = requests.post(
                    "http://localhost:8000/api/v1/token",
                    data={"username": email, "password": password}
                )
                if res.status_code == 200:
                    token = res.json().get("access_token")
                    st.session_state["token"] = token
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            except Exception as e:
                st.error(f"Connection failed: {e}")

if not st.session_state["token"]:
    login()
    st.stop()

# --- Authenticated Dashboard ---

# 1. Sidebar Controls
with st.sidebar:
    st.header("Dashboard Settings")
    mode = st.radio("Optimization Mode", ["Economic Mode 💰", "Green Mode 🌿"], 
                    help="Economic: Minimize cost. Green: Maximize self-consumption.")
    
    st.divider()
    if st.button("Logout"):
        st.session_state["token"] = None
        st.rerun()

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