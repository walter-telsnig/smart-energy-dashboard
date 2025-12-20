# ==============================================
# File: ui/app.py
# ==============================================
"""
Smart Energy Dashboard — Streamlit multipage entry.

Why this structure:
- Keep a single entry at ui/app.py.
- Feature pages under ui/pages/ (native Streamlit multipage).
- Each page uses tabs internally for different views (chart, stats, preview).

Run:
  streamlit run ui/app.py

Notes:
- Pages expect CSVs in infra/data/* but can be switched to API calls where available.
- Keep this file light; most logic lives in the pages.
"""
# from ui.utils.overview_metrics import count_csv_files, count_csv_rows, total_pv_kwh
from __future__ import annotations
import streamlit as st
from pathlib import Path
import pandas as pd

st.set_page_config(page_title="Smart Energy Dashboard", layout="wide")

import importlib.util

def _load_auth():
    auth_path = Path(__file__).resolve().parent / "auth.py"  # ui/auth.py
    spec = importlib.util.spec_from_file_location("auth", auth_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load auth module from {auth_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

auth = _load_auth()
# st.write("AUTH FILE:", getattr(auth, "__file__", "no file"))
# st.write("AUTH EXPORTS:", [x for x in dir(auth) if "logout" in x or "login" in x])

auth.require_login()
auth.logout_button()

st.title("🔆 Smart Energy Dashboard")
st.caption("PV • Prices • Consumption • Battery Simulation")

DATA_DIR = Path("infra/data")

cols = st.columns(3)
paths = {
    "PV": DATA_DIR / "pv",
    "Market": DATA_DIR / "market",
    "Consumption": DATA_DIR / "consumption",
}

with cols[0]:
    st.subheader("Data Folders")
    for name, p in paths.items():
        exists = p.exists()
        st.write(("✅" if exists else "❌"), name, f"→ {p}")

with cols[1]:
    st.subheader("Tips")
    st.markdown("- Use the left sidebar to navigate pages. - Keep all CSV timestamps in UTC.")

with cols[2]:
    st.subheader("Next")
    st.markdown("- Try **Battery Sim** page after selecting PV + Consumption windows and parameters.")

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