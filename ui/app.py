"""
Smart Energy Dashboard — PV Viewer (M1 Demo)
Read-only Streamlit UI that consumes the FastAPI backend.

Design notes:
- SRP: UI only talks to the REST API, never the DB or modules directly.
- ADP: UI depends on API boundary; backend does not import UI.
- OCP: API contract normalized (timestamp/value) → UI is decoupled from CSV specifics.
"""

import os
from typing import Dict, List

import pandas as pd
import requests
import streamlit as st


# ---------- Config ------------------------------------------------------------

API_BASE = os.getenv("API_BASE", "http://localhost:8000/api/v1").rstrip("/")
APP_TITLE = "Smart Energy Dashboard — PV Viewer (M1 Demo)"

st.set_page_config(page_title=APP_TITLE, layout="wide")


# ---------- Helpers -----------------------------------------------------------

def api_get(path: str, **params) -> Dict:
    """Simple JSON GET with basic error handling."""
    url = f"{API_BASE}/{path.lstrip('/')}"
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=60)
def fetch_catalog() -> List[Dict]:
    """Fetch and cache the PV catalog for 60s."""
    data = api_get("pv/catalog")
    items = data.get("items") or data.get("series") or []
    # Normalize keys (drop .csv suffix if present)
    out = []
    for it in items:
        key = it.get("key") or it.get("name") or it.get("id")
        if not key:
            continue
        if key.endswith(".csv"):
            key = key[:-4]
        out.append({"key": key, **it})
    return out


def fetch_head(key: str, n: int) -> pd.DataFrame:
    """Fetch the first n rows and return a normalized DataFrame with columns: timestamp, value."""
    data = api_get("pv/head", key=key, n=n)
    rows = data.get("rows") or data.get("points") or []
    df = pd.DataFrame(rows)

    if df.empty:
        return pd.DataFrame(columns=["timestamp", "value"])

    # Normalize header defensively
    cols_lower = {c.lower(): c for c in df.columns}
    ts = cols_lower.get("timestamp") or cols_lower.get("time") or cols_lower.get("date") or df.columns[0]
    if "value" in cols_lower:
        val = cols_lower["value"]
    else:
        numeric = [c for c in df.columns if c != ts and pd.api.types.is_numeric_dtype(df[c])]
        val = numeric[0] if numeric else df.columns[1] if len(df.columns) > 1 else df.columns[0]

    df = df.rename(columns={ts: "timestamp", val: "value"})
    return df[["timestamp", "value"]]


# ---------- UI ----------------------------------------------------------------

# Header
st.title(APP_TITLE)

# Health badge (use API root without /api/v1 to call /health)
try:
    api_root = API_BASE.removesuffix("/api/v1")
    hr = requests.get(f"{api_root}/health", timeout=5)
    ok = (hr.status_code == 200 and (hr.json().get("status") == "ok"))
    if ok:
        st.success("API healthy")
    else:
        st.warning(f"API health not ok: {hr.text}")
except Exception as e:
    st.error(f"API not reachable: {e}")

# Sidebar controls
with st.sidebar:
    st.header("Controls")
    st.caption(f"API base: {API_BASE}")

    try:
        catalog = fetch_catalog()
        keys = [it["key"] for it in catalog]
    except Exception as e:
        catalog, keys = [], []
        st.error(f"Failed to load catalog: {e}")

    sel_key = st.selectbox("Select series", keys, index=0 if keys else None, placeholder="Choose a CSV…")
    n = st.slider("Head (n rows)", min_value=24, max_value=7 * 24, value=48, step=24)

    show_table = st.checkbox("Show data table", value=False)
    show_stats = st.checkbox("Show KPIs", value=True)

# Main content
load_clicked = st.button("Load", use_container_width=True)

if load_clicked and sel_key:
    try:
        df = fetch_head(sel_key, n)
        if df.empty:
            st.warning("No data returned.")
        else:
            # KPIs
            if show_stats:
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Rows", len(df))
                with c2:
                    st.metric("Min", f"{df['value'].min():.2f}")
                with c3:
                    st.metric("Max", f"{df['value'].max():.2f}")

            # Chart
            st.subheader("Series")
            # Ensure timestamp is string-like index for Streamlit
            chart_df = df.copy()
            chart_df["timestamp"] = chart_df["timestamp"].astype(str)
            st.line_chart(chart_df.set_index("timestamp")["value"])

            # Optional table
            if show_table:
                st.subheader("Data")
                st.dataframe(df, use_container_width=True, height=340)

            # Download
            csv_bytes = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download CSV (current view)",
                data=csv_bytes,
                file_name=f"{sel_key}_head_{n}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    except requests.HTTPError as http_err:
        st.error(f"API error {http_err.response.status_code}: {http_err.response.text}")
    except Exception as e:
        st.error(f"Request failed: {e}")

# Footer
st.caption("Milestone 1 — Read-only demo UI. For M2 we’ll add tests, quality gates, and more endpoints.")
