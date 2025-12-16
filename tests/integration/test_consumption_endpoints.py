from fastapi.testclient import TestClient
from app.main import create_app

client = TestClient(create_app())


def test_consumption_catalog():
    resp = client.get("/api/v1/consumption/catalog")
    assert resp.status_code == 200

    data = resp.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0


def test_consumption_head():
    resp = client.get(
        "/api/v1/consumption/head",
        params={"key": "consumption_2025_hourly", "n": 24},
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data["count"] == 24
    assert "rows" in data
    assert "timestamp" in data["rows"][0]
    assert "value" in data["rows"][0]


def test_consumption_full_series_limited():
    resp = client.get(
        "/api/v1/consumption",
        params={"key": "consumption_2025_hourly", "limit": 100},
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data["count"] == 100
