# tests/integration/test_auth_api.py
from __future__ import annotations

from ui.utils import auth_api


class DummyResp:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


def test_api_login_success(monkeypatch):
    def fake_post(url, data=None, timeout=10):
        assert url.endswith("/api/v1/token")
        return DummyResp(200, {"access_token": "abc"})

    monkeypatch.setattr(auth_api.requests, "post", fake_post)

    ok, msg, token = auth_api.api_login("user@example.com", "pw", "http://localhost:8000")
    assert ok is True
    assert token == "abc"


def test_api_login_fail(monkeypatch):
    def fake_post(url, data=None, timeout=10):
        return DummyResp(401, {}, "Unauthorized")

    monkeypatch.setattr(auth_api.requests, "post", fake_post)

    ok, msg, token = auth_api.api_login("user@example.com", "pw", "http://localhost:8000")
    assert ok is False
    assert token == ""


def test_api_register_success(monkeypatch):
    def fake_post(url, json=None, timeout=10):
        assert url.endswith("/api/v1/accounts/")
        return DummyResp(201, {"id": 1})

    monkeypatch.setattr(auth_api.requests, "post", fake_post)

    ok, msg = auth_api.api_register("user@example.com", "pw", "User", "http://localhost:8000")
    assert ok is True


def test_api_register_conflict(monkeypatch):
    def fake_post(url, json=None, timeout=10):
        return DummyResp(409, {}, "Conflict")

    monkeypatch.setattr(auth_api.requests, "post", fake_post)

    ok, msg = auth_api.api_register("user@example.com", "pw", "User", "http://localhost:8000")
    assert ok is False
    assert "already exists" in msg.lower()
