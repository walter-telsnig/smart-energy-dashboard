from fastapi.testclient import TestClient
from app.main import create_app

def test_timeseries_merged_endpoint():
    app = create_app()
    client = TestClient(app)

    r = client.get("/api/v1/timeseries/merged?year=2026&limit=10")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 10
    assert "datetime" in data[0]
    assert "pv_kw" in data[0]
    assert "load_kwh" in data[0]
    assert "price_eur_kwh" in data[0]
