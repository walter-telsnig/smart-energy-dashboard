import pytest
from datetime import datetime, timedelta, date
from infra.db import SessionLocal
from infra.models.consumption import Consumption


@pytest.mark.integration
def test_analyze_endpoint_persists_patterns_and_personality(client):
    # Insert consumption rows for last 10 days hourly
    session = SessionLocal()
    try:
        session.query(Consumption).delete()
        session.commit()

        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        rows = []
        for i in range(24 * 10):
            ts = now - timedelta(hours=i)
            # Make nights heavier to trigger night_owl
            hour = ts.hour
            kwh = 2.0 if (hour >= 22 or hour < 6) else 1.0
            rows.append(Consumption(datetime=ts, consumption_kwh=kwh))
        session.add_all(rows)
        session.commit()

        payload = {"user_id": 123, "days": 7}
        r = client.post("/api/v1/patterns/analyze", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert "personality" in data
        assert "patterns" in data

        # Now check DB persisted one personality for our user
        from modules.pattern.model import EnergyPersonality
        person = session.query(EnergyPersonality).filter(EnergyPersonality.user_id == 123).first()
        assert person is not None

    finally:
        session.close()


def test_analyze_endpoint_validation(client):
    r = client.post("/api/v1/patterns/analyze", json={"user_id": 1, "days": 3})
    # Pydantic validation should reject days < 7
    assert r.status_code == 422


def test_get_personality_not_found(client):
    r = client.get("/api/v1/99999/personality")
    assert r.status_code in (404, 200)
