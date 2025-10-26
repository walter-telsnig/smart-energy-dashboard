from fastapi.testclient import TestClient
from app.main import create_app

client = TestClient(create_app())

def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
