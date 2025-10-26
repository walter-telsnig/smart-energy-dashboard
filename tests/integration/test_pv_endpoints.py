from fastapi.testclient import TestClient
from app.main import create_app

client = TestClient(create_app())


def test_catalog_ok():
    r = client.get("/api/v1/pv/catalog")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    # Non-fatal if empty (repo without CSVs), but assert shape
    assert isinstance(data["items"], list)


def test_head_ok_when_key_exists_or_skip():
    # Discover a real key from catalog, then call /head
    r = client.get("/api/v1/pv/catalog")
    assert r.status_code == 200
    items = r.json().get("items", [])
    if not items:
        # Skip gracefully if no CSVs in infra/data/pv (e.g., clean CI)
        import pytest
        pytest.skip("No CSVs in infra/data/pv — skipping PV head test")

    key = items[0]["key"]
    r2 = client.get("/api/v1/pv/head", params={"key": key, "n": 24})
    assert r2.status_code == 200
    data = r2.json()
    assert "rows" in data and isinstance(data["rows"], list)
    # If rows exist, check normalized schema
    if data["rows"]:
        row = data["rows"][0]
        assert "timestamp" in row and "value" in row


def test_head_404_unknown_key():
    r = client.get("/api/v1/pv/head", params={"key": "___does_not_exist___", "n": 24})
    assert r.status_code == 404
