import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from infra.database import Base, engine
from datetime import datetime, timedelta

client = TestClient(create_app())
start = datetime(2025,1,1)
end = start + timedelta(days=7)

@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    Base.metadata.create_all(bind=engine)
    #Run test
    yield
    Base.metadata.drop_all(bind=engine)

def test_pv_minute_db_get():
    resp = client.get(
        "/api/dataManagment/pv_minute-db/list",
        params={
            "start": start,
            "end": end
        },
    )
    assert resp.status_code == 200

    data = resp.json()
    assert len(data) == 673

def test_pv_minute_db_get_error():
    resp = client.get(
        "/api/dataManagment/pv_minute-db/list",
    )

    assert resp.status_code != 200
