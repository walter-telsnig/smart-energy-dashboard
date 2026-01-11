# ui/utils/auth_api.py
from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple

import requests

API_DEFAULT = "http://localhost:8000"
_TIMEOUT_S = 10


def api_base(api_base_url: str | None = None) -> str:
    """
    Returns normalized API base URL.
    Priority:
      1) api_base_url passed in
      2) env var API_BASE_URL
      3) default
    """
    return (api_base_url or os.getenv("API_BASE_URL") or API_DEFAULT).rstrip("/")


def _post(
    url: str,
    *,
    data: Optional[Dict[str, Any]] = None,
    json: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str, Optional[requests.Response]]:
    """Small wrapper to keep error handling consistent and avoid duplication."""
    try:
        resp = requests.post(url, data=data, json=json, timeout=_TIMEOUT_S)
        return True, "", resp
    except Exception as e:
        return False, f"Could not reach API: {e}", None


def api_login(email: str, password: str, api_base_url: str | None = None) -> Tuple[bool, str, str]:
    base = api_base(api_base_url)
    url = f"{base}/api/v1/token"

    ok, err, resp = _post(url, data={"username": email, "password": password})
    if not ok or resp is None:
        return False, err, ""

    if resp.status_code != 200:
        return False, f"Login failed ({resp.status_code}): {resp.text}", ""

    token = resp.json().get("access_token")
    if not token:
        return False, "Login succeeded but access_token missing.", ""

    return True, "Logged in.", token


def api_register(
    email: str, password: str, full_name: str, api_base_url: str | None = None
) -> Tuple[bool, str]:
    base = api_base(api_base_url)
    url = f"{base}/api/v1/accounts/"

    payload = {"email": email, "password": password, "full_name": full_name}
    ok, err, resp = _post(url, json=payload)
    if not ok or resp is None:
        return False, err

    if resp.status_code in (200, 201):
        return True, "Account created successfully."
    if resp.status_code == 409:
        return False, "User already exists with this email."

    return False, f"Registration failed ({resp.status_code}): {resp.text}"