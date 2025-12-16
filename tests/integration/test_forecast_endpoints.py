from fastapi.testclient import TestClient
from app.main import create_app

client = TestClient(create_app())


def test_forecast_endpoint_exists():
    resp = client.get("/api/v1/forecast")
    assert resp.status_code == 200

    data = resp.json()
    assert "rows" in data
    assert isinstance(data["rows"], list)


def test_forecast_row_shape():
    resp = client.get("/api/v1/forecast")
    assert resp.status_code == 200

    rows = resp.json()["rows"]
    assert len(rows) > 0

    row = rows[0]
    assert "timestamp" in row
    assert "value" in row
