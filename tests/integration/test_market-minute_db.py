from fastapi.testclient import TestClient
from app.main import create_app
from infra.models import Market_Minute as Market_Minute
from datetime import datetime, timedelta

#client = TestClient(create_app())
start = datetime(2025,1,1)
end = start + timedelta(days=7)

def test_market_minute_db_get(client):
    resp = client.get(
        "/api/dataManagment/price_minute-db/list",
        params={
            "start": start,
            "end": end
        },
    )
    assert resp.status_code == 200

    data = resp.json()
    assert len(data) == 673

def test_market_minute_db_get_error(client):
    resp = client.get(
        "/api/dataManagment/price_minute-db/list",
    )

    assert resp.status_code != 200
