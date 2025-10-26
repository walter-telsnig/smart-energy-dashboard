import os, requests, pandas as pd, streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000/api/v1")

st.set_page_config(page_title="Smart Energy Dashboard — PV", layout="wide")
st.title("Smart Energy Dashboard — PV Viewer (M1 Demo)")

# Health badge
try:
    hr = requests.get(f"{API_BASE.replace('/api/v1','')}/health", timeout=3)
    ok = (hr.status_code == 200 and hr.json().get("status") == "ok")
    if ok:
        st.success("API healthy")
    else:
        st.warning(f"API health not ok: {hr.text}")
except Exception as e:
    st.error(f"API not reachable: {e}")

# Catalog
@st.cache_data(ttl=60)
def fetch_catalog():
    r = requests.get(f"{API_BASE}/pv/catalog", timeout=5)
    r.raise_for_status()
    return r.json()

try:
    cat = fetch_catalog()
    keys = [it["key"] for it in cat.get("items", [])]
except Exception as e:
    keys = []
    st.error(f"Failed to load catalog: {e}")

sel = st.selectbox("Select series", keys, index=0 if keys else None, placeholder="Choose a CSV…")
n = st.slider("Head (n rows)", 24, 168, 48, step=24)

col1, col2 = st.columns([1,2])
if col1.button("Load", use_container_width=True) and sel:
    try:
        r = requests.get(f"{API_BASE}/pv/head", params={"key": sel, "n": n}, timeout=10)
        if r.status_code != 200:
            st.error(f"API error {r.status_code}: {r.text}")
        else:
            rows = r.json().get("rows", [])
            if not rows:
                st.warning("No data rows returned.")
            else:
                df = pd.DataFrame(rows)
                with col2:
                    st.metric("Rows", len(df))
                st.line_chart(df.set_index("timestamp")["value"])
                st.dataframe(df, use_container_width=True, height=300)
    except Exception as e:
        st.error(f"Request failed: {e}")

st.caption(f"API base: {API_BASE}")
