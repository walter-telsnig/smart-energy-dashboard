# ui/utils/auth_api.py
from __future__ import annotations

import os
from typing import Tuple

import requests

API_DEFAULT = "http://localhost:8000"


def api_base(api_base_url: str | None = None) -> str:
    """
    Returns normalized API base URL.
    Priority:
      1) api_base_url passed in
      2) env var API_BASE_URL
      3) default
    """
    base = (api_base_url or os.getenv("API_BASE_URL") or API_DEFAULT).rstrip("/")
    return base


def api_login(email: str, password: str, api_base_url: str | None = None) -> Tuple[bool, str, str]:
    base = api_base(api_base_url)
    url = f"{base}/api/v1/token"
    try:
        r = requests.post(url, data={"username": email, "password": password}, timeout=10)
        if r.status_code != 200:
            return False, f"Login failed ({r.status_code}): {r.text}", ""
        token = r.json().get("access_token")
        if not token:
            return False, "Login succeeded but access_token missing.", ""
        return True, "Logged in.", token
    except Exception as e:
        return False, f"Could not reach API: {e}", ""


def api_register(
    email: str, password: str, full_name: str, api_base_url: str | None = None
) -> Tuple[bool, str]:
    base = api_base(api_base_url)
    url = f"{base}/api/v1/accounts/"
    try:
        payload = {"email": email, "password": password, "full_name": full_name}
        r = requests.post(url, json=payload, timeout=10)

        if r.status_code in (200, 201):
            return True, "Account created successfully."
        if r.status_code == 409:
            return False, "User already exists with this email."
        return False, f"Registration failed ({r.status_code}): {r.text}"
    except Exception as e:
        return False, f"Could not reach API: {e}"
