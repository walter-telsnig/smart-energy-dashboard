import pytest
from modules.pattern.domain import EnergyPattern, EnergyPersonality, PatternType, PersonalityType
from datetime import datetime, date


def test_energy_pattern_validation_confidence_bounds():
    with pytest.raises(ValueError):
        EnergyPattern(id=None, user_id=1, pattern_type=PatternType.NIGHT_OWL, confidence=1.5,
                      description="", detected_at=datetime.now(), start_date=date.today(), end_date=date.today())

    with pytest.raises(ValueError):
        EnergyPattern(id=None, user_id=1, pattern_type=PatternType.NIGHT_OWL, confidence=-0.1,
                      description="", detected_at=datetime.now(), start_date=date.today(), end_date=date.today())


def test_energy_pattern_start_end_date_validation():
    with pytest.raises(ValueError):
        EnergyPattern(id=None, user_id=1, pattern_type=PatternType.NIGHT_OWL, confidence=0.5,
                      description="", detected_at=datetime.now(), start_date=date.today(), end_date=date(2020,1,1))


def test_priority_property():
    p_high = EnergyPattern(id=None, user_id=1, pattern_type=PatternType.NIGHT_OWL, confidence=0.85,
                            description="", detected_at=datetime.now(), start_date=date.today(), end_date=date.today())
    assert p_high.priority == "high"

    p_med = EnergyPattern(id=None, user_id=1, pattern_type=PatternType.NIGHT_OWL, confidence=0.6,
                           description="", detected_at=datetime.now(), start_date=date.today(), end_date=date.today())
    assert p_med.priority == "medium"

    p_low = EnergyPattern(id=None, user_id=1, pattern_type=PatternType.NIGHT_OWL, confidence=0.2,
                           description="", detected_at=datetime.now(), start_date=date.today(), end_date=date.today())
    assert p_low.priority == "low"


def test_energy_personality_invariants_and_display_name():
    with pytest.raises(ValueError):
        EnergyPersonality(id=None, user_id=1, personality_type=PersonalityType.BALANCED_USER, emoji="",
                          score=50, description="", dominant_patterns=[], detected_at=datetime.now())

    with pytest.raises(ValueError):
        EnergyPersonality(id=None, user_id=1, personality_type=PersonalityType.BALANCED_USER, emoji="⚖️",
                          score=200, description="", dominant_patterns=[], detected_at=datetime.now())

    p = EnergyPersonality(id=None, user_id=1, personality_type=PersonalityType.NIGHT_OWL, emoji="🦉",
                          score=80, description="", dominant_patterns=["night_owl"], detected_at=datetime.now())
    assert "Night Owl" in p.display_name
