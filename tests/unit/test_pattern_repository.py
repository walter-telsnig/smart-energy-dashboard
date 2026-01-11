from infra.db import SessionLocal
from infra.pattern.repository import SQLAlchemyPatternRepository, SQLAlchemyPersonalityRepository
from infra.models.consumption import Consumption
from infra.models.pv import PV
from datetime import datetime, timedelta, date


def test_get_consumption_and_pv_data_and_save_pattern_personality():
    session = SessionLocal()
    try:
        # Clean up tables used (simple approach for tests)
        session.query(Consumption).delete()
        session.query(PV).delete()
        session.commit()

        # Insert consumption data for 3 days hourly
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        rows = []
        for i in range(24 * 3):
            ts = now - timedelta(hours=i)
            rows.append(Consumption(datetime=ts, consumption_kwh=1.0))
        session.add_all(rows)
        session.commit()

        # Insert pv data
        pv_rows = [PV(datetime=now - timedelta(hours=i), production_kw=0.5) for i in range(24 * 3)]
        session.add_all(pv_rows)
        session.commit()

        repo = SQLAlchemyPatternRepository(session)
        cdata = repo.get_consumption_data(1, date.today() - timedelta(days=3), date.today())
        pdata = repo.get_pv_data(1, date.today() - timedelta(days=3), date.today())

        assert len(cdata) > 0
        assert len(pdata) > 0

        # Test creating a pattern via repo
        from modules.pattern.domain import EnergyPattern, PatternType
        p = EnergyPattern(id=None, user_id=1, pattern_type=PatternType.NIGHT_OWL, confidence=0.8,
                          description="x", detected_at=datetime.now(), start_date=date.today(), end_date=date.today())
        saved = repo.create_pattern(p)
        assert saved.id is None or saved.user_id == 1

        # Personality repo
        person_repo = SQLAlchemyPersonalityRepository(session)
        from modules.pattern.domain import EnergyPersonality, PersonalityType
        person = EnergyPersonality(id=None, user_id=2, personality_type=PersonalityType.NIGHT_OWL, emoji="🦉", score=80,
                                   description="x", dominant_patterns=["night_owl"], detected_at=datetime.now())
        saved_person = person_repo.save_personality(person)
        assert saved_person.user_id == 2

    finally:
        session.close()
