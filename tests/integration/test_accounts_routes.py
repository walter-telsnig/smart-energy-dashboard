from fastapi.testclient import TestClient
from app.main import app
from infra.db import Base, engine

client = TestClient(app)

def setup_module(_):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def test_crud_flow():
    # Create
    r = client.post("/api/v1/accounts/", json={"email": "bob@example.com", "full_name": "Bob"})
    assert r.status_code == 201
    uid = r.json()["id"]

    # Read
    assert client.get(f"/api/v1/accounts/{uid}").status_code == 200
    assert client.get("/api/v1/accounts/").status_code == 200

    # Update
    r = client.patch(f"/api/v1/accounts/{uid}", params={"full_name": "Bobby"})
    assert r.status_code == 200
    assert r.json()["full_name"] == "Bobby"

    # Delete
    assert client.delete(f"/api/v1/accounts/{uid}").status_code == 204
    assert client.get(f"/api/v1/accounts/{uid}").status_code == 404
