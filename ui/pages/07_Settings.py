# ui/pages/07_Settings.py
from __future__ import annotations
import streamlit as st
from utils.theme import apply_global_style, sidebar_nav
from utils.settings import load_settings, save_settings

st.set_page_config(layout="wide", page_title="Settings • Smart Energy Dashboard", page_icon="⚙️")

apply_global_style()
sidebar_nav(active="Settings")

if "token" not in st.session_state or not st.session_state["token"]:
    st.switch_page("pages/00_Login.py")

st.title("⚙️ Settings")

s = load_settings()

with st.form("settings_form"):
    default_view_mode = st.radio(
        "Default view mode",
        ["Daily View", "Hourly View"],
        index=0 if s["default_view_mode"] == "Daily View" else 1
    )

    default_range_days = st.slider("Default date range (days)", 1, 30, int(s["default_range_days"]))
    recommend_block_hours = st.slider("Recommended run window length (hours)", 1, 8, int(s["recommend_block_hours"]))

    dev_show_api_base = st.checkbox("Developer: show API base input", value=bool(s["dev_show_api_base"]))

    saved = st.form_submit_button("Save settings")

if saved:
    save_settings({
        "default_view_mode": default_view_mode,
        "default_range_days": default_range_days,
        "recommend_block_hours": recommend_block_hours,
        "dev_show_api_base": dev_show_api_base,
    })
    st.success("Saved ✅")
