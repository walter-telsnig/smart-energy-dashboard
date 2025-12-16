from fastapi.testclient import TestClient
from app.main import create_app

client = TestClient(create_app())


def test_market_catalog():
    resp = client.get("/api/v1/market/catalog")
    assert resp.status_code == 200

    data = resp.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) > 0


def test_market_head():
    resp = client.get(
        "/api/v1/market/head",
        params={"key": "price_2027_hourly", "n": 24},
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data["count"] == 24
    assert "rows" in data
    assert "timestamp" in data["rows"][0]
    assert "value" in data["rows"][0]


def test_market_full_series_limited():
    resp = client.get(
        "/api/v1/market",
        params={"key": "price_2027_hourly", "limit": 48},
    )
    assert resp.status_code == 200

    data = resp.json()
    assert data["count"] == 48
