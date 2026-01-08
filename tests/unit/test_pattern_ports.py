import pytest
from modules.pattern.ports import PatternRepositoryPort, PersonalityRepositoryPort
from modules.pattern.domain import EnergyPattern, EnergyPersonality, PatternType, PersonalityType
from datetime import datetime, date


def test_ports_are_abstract():
    with pytest.raises(TypeError):
        PatternRepositoryPort()
    with pytest.raises(TypeError):
        PersonalityRepositoryPort()


class DummyRepo(PatternRepositoryPort):
    def create_pattern(self, pattern: EnergyPattern) -> EnergyPattern:
        return pattern
    def get_user_patterns(self, user_id: int, limit: int = 100, offset: int = 0):
        return []
    def get_consumption_data(self, user_id: int, start_date: date, end_date: date):
        return []
    def get_pv_data(self, user_id: int, start_date: date, end_date: date):
        return []


class DummyPersonalityRepo(PersonalityRepositoryPort):
    def save_personality(self, personality: EnergyPersonality) -> EnergyPersonality:
        return personality
    def get_personality(self, user_id: int):
        return None


def test_dummy_repo_works():
    dr = DummyRepo()
    from datetime import timedelta
    now = datetime.now()
    # Should return what we pass to create_pattern
    p = EnergyPattern(id=None, user_id=1, pattern_type=PatternType.NIGHT_OWL, confidence=0.8,
                      description="", detected_at=now, start_date=date.today(), end_date=date.today())
    assert dr.create_pattern(p) is p

    pr = DummyPersonalityRepo()
    person = EnergyPersonality(id=None, user_id=1, personality_type=PersonalityType.BALANCED_USER, emoji="⚖️",
                               score=50, description="", dominant_patterns=[], detected_at=now)
    assert pr.save_personality(person) is person
