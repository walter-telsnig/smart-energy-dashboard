# ui/pages/00_Health.py
"""
Health Check:
- Checks expected data folders and sample CSV readability.
- Optionally pings API endpoints to confirm they are reachable.
- Shows environment basics (Python, pandas, Streamlit).
"""

from __future__ import annotations
import streamlit as st
from pathlib import Path
import importlib
import platform
import pandas as pd
import requests

st.set_page_config(layout="wide")
st.title("🩺 Health Check")

# --- Filesystem checks ---
st.subheader("Folders")
rows = []
for label, p in {
    "PV": Path("infra/data/pv"),
    "Market": Path("infra/data/market"),
    "Consumption": Path("infra/data/consumption"),
}.items():
    rows.append((label, str(p), "✅" if p.exists() else "❌"))
st.table(pd.DataFrame(rows, columns=["Name", "Path", "Exists"]))

st.subheader("CSV Readability (optional)")
pv_csv = st.text_input("PV CSV", "infra/data/pv/pv_2025_hourly.csv")
price_csv = st.text_input("Price CSV", "infra/data/market/price_2025_hourly.csv")
cons_csv = st.text_input("Consumption CSV", "infra/data/consumption/consumption_2025_hourly.csv")

def try_read(path: str, n: int = 3) -> tuple[str, str]:
    try:
        df = pd.read_csv(path, nrows=n)
        return ("✅", f"Columns: {list(df.columns)}")
    except Exception as e:
        return ("❌", str(e))

if st.button("Test CSVs"):
    for label, p in [("PV", pv_csv), ("Price", price_csv), ("Consumption", cons_csv)]:
        ok, info = try_read(p)
        st.write(f"{ok} {label}: {p}")
        st.caption(info)

# --- API checks ---
st.subheader("API Endpoints")
api_base = st.text_input("API base", "http://localhost:8000")

def ping(path: str) -> tuple[str, str]:
    url = f"{api_base}{path}"
    try:
        r = requests.get(url, timeout=5) if path.endswith("/defaults") else requests.get(url, timeout=5)
        if r.status_code == 200:
            return ("✅", f"200 OK")
        return ("❌", f"{r.status_code} {r.text[:120]}")
    except Exception as e:
        return ("❌", str(e))

col1, col2 = st.columns(2)
with col1:
    if st.button("Ping /api/v1/battery/defaults"):
        ok, info = ping("/api/v1/battery/defaults")
        st.write(f"{ok} /battery/defaults — {info}")
with col2:
    if st.button("Ping (example) /api/v1/pv/catalog"):
        try:
            r = requests.get(f"{api_base}/api/v1/pv/catalog", timeout=5)
            st.write(("✅" if r.status_code == 200 else "❌"), "/pv/catalog —", r.status_code)
            if r.ok:
                st.json(r.json())
        except Exception as e:
            st.write("❌ /pv/catalog —", e)

# --- Environment info ---
st.subheader("Environment")
rows = [
    ("Python", platform.python_version()),
]
for pkg in ("pandas", "streamlit", "requests"):
    try:
        mod = importlib.import_module(pkg)
        rows.append((pkg, getattr(mod, "__version__", "?")))
    except Exception:
        rows.append((pkg, "not installed"))
st.table(pd.DataFrame(rows, columns=["Component", "Version"]))
