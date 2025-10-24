# Streamlit demo UI (read-only) for Milestone 1
# Run: streamlit run ui/app.py
import os
import requests
import pandas as pd
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000/api/v1")

st.title("Smart Energy Dashboard — PV Viewer (M1 Demo)")

# 1) Catalog
cat = requests.get(f"{API_BASE}/pv/catalog").json()
keys = [row["key"] for row in cat.get("items", [])]
sel = st.selectbox("Select series", keys)

n = st.slider("Head (n rows)", 24, 168, 48, step=24)  # 1–7 days hourly
if st.button("Load"):
    r = requests.get(f"{API_BASE}/pv/head", params={"key": sel, "n": n})
    if r.status_code == 200:
        df = pd.DataFrame(r.json()["rows"])
        st.line_chart(df.set_index("timestamp")["value"])
    else:
        st.error(f"API error {r.status_code}: {r.text}")