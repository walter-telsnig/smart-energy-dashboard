from fastapi.testclient import TestClient
from app.main import create_app
from datetime import datetime, timedelta

client = TestClient(create_app())
start = datetime(2025,1,1)
end = start + timedelta(days=7)

def test_consumption_db_get():
    resp = client.get(
        "/api/dataManagment/consumption-db/list",
        params={
            "start": start,
            "end": end
        },
    )
    assert resp.status_code == 200

    data = resp.json()
    assert len(data) == 169

def test_consumption_db_get_error():
    resp = client.get(
        "/api/dataManagment/consumption-db/list",
    )

    assert resp.status_code != 200
