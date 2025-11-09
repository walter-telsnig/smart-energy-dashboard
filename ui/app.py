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
from __future__ import annotations
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Smart Energy Dashboard", layout="wide")

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