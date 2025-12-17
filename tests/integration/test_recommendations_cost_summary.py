from fastapi.testclient import TestClient
from app.main import create_app

client = TestClient(create_app())


def test_cost_summary_endpoint_exists():
    resp = client.get("/api/v1/recommendations/cost-summary")
    assert resp.status_code == 200


def test_cost_summary_shape():
    resp = client.get("/api/v1/recommendations/cost-summary")
    data = resp.json()

    assert "hours" in data
    assert "baseline_cost_eur" in data
    assert "optimized_cost_eur" in data
    assert "savings_eur" in data
    assert "savings_percent" in data

    assert data["baseline_cost_eur"] >= 0
    assert data["optimized_cost_eur"] >= 0


def test_cost_summary_savings_logic():
    resp = client.get(
        "/api/v1/recommendations/cost-summary",
        params={"hours": 24, "price_threshold_eur_kwh": 0.12},
    )
    data = resp.json()

    # Optimized should never be more expensive in v1
    assert data["optimized_cost_eur"] <= data["baseline_cost_eur"]
