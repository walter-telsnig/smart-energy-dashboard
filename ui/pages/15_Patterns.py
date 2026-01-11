import os
import streamlit as st
import requests
import pandas as pd
from utils.theme import apply_global_style, sidebar_nav

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(layout="wide", page_title="Patterns • Smart Energy Dashboard", page_icon="🔍")
apply_global_style()
sidebar_nav(active="🔍 Patterns")

# Require login like other pages
if "token" not in st.session_state or not st.session_state["token"]:
    st.switch_page("pages/00_Login.py")

st.title("🔍 Energy Pattern Analysis")

user_id = st.number_input("User ID", value=1, min_value=1, step=1)
days = st.slider("History (days)", min_value=7, max_value=90, value=30)
if st.button("Run analysis"):
    path = f"{API_BASE_URL}/api/v1/patterns/analyze"
    payload = {"user_id": int(user_id), "days": int(days)}
    headers = {"Authorization": f"Bearer {st.session_state.get('token')}"} if st.session_state.get("token") else {}
    with st.spinner("Analyzing patterns..."):
        try:
            r = requests.post(path, json=payload, headers=headers, timeout=20)
            r.raise_for_status()
            data = r.json()
            st.success(data.get("summary", "Analysis complete"))

            # Personality
            person = data.get("personality", {})
            col1, col2 = st.columns([1, 3])
            with col1:
                st.metric("Score", person.get("score", "-"))
                st.markdown(f"### {person.get('emoji','')}")
            with col2:
                st.write(person.get("display_name", ""))
                st.write(person.get("description", ""))

            # Patterns table
            patterns = data.get("patterns", [])
            if patterns:
                df = pd.DataFrame(patterns)
                st.table(df[["pattern_type", "confidence", "priority", "description"]])
            else:
                st.info("No patterns detected.")

        except requests.exceptions.RequestException as e:
            st.error(f"API error: {e}")