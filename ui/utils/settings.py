# ui/utils/settings.py
from __future__ import annotations

import json
from pathlib import Path
import streamlit as st

SETTINGS_FILE = Path("ui/.user_settings.json")

DEFAULT_SETTINGS = {
    "default_view_mode": "Hourly View",  # "Daily View" or "Hourly View"
    "default_range_days": 7,  # default date range on pages
    "recommend_block_hours": 4,  # suggest run window length (e.g., 4h)
    "dev_show_api_base": False,  # hide API base input by default
}


def _current_user_key() -> str:
    # Prefer auth_email if available
    return str(st.session_state.get("auth_email") or "anonymous").lower().strip()


def load_settings() -> dict:
    user = _current_user_key()
    if not SETTINGS_FILE.exists():
        return DEFAULT_SETTINGS.copy()

    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        user_settings = data.get(user, {})
        merged = DEFAULT_SETTINGS.copy()
        merged.update(user_settings)
        return merged
    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_settings(new_settings: dict) -> None:
    user = _current_user_key()
    data = {}
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    data[user] = {**(data.get(user, {})), **new_settings}
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_setting(name: str):
    s = load_settings()
    return s.get(name, DEFAULT_SETTINGS.get(name))
