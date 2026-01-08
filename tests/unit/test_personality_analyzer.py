from modules.pattern.services.personality_analyzer import PersonalityAnalyzer
from modules.pattern.domain import EnergyPattern, PatternType
from datetime import datetime, date


def make_pattern(p_type: PatternType, conf: float):
    return EnergyPattern(
        id=None,
        user_id=1,
        pattern_type=p_type,
        confidence=conf,
        description="",
        detected_at=datetime.now(),
        start_date=date.today(),
        end_date=date.today()
    )


def test_default_personality_when_no_patterns():
    pa = PersonalityAnalyzer()
    p = pa.create_from_patterns(1, [])
    assert p.personality_type.name.lower() == "balanced_user"
    assert p.score == 50


def test_personality_mapping_and_score():
    pa = PersonalityAnalyzer()
    patterns = [
        make_pattern(PatternType.NIGHT_OWL, 0.8),
        make_pattern(PatternType.NIGHT_OWL, 0.6),
        make_pattern(PatternType.MORNING_BIRD, 0.5),
    ]
    personality = pa.create_from_patterns(42, patterns)
    assert personality.personality_type.name.lower().startswith("night")
    # Score should be average confidence of relevant patterns * 100
    assert 0 < personality.score <= 100
    assert personality.emoji is not None
    assert isinstance(personality.dominant_patterns, list)
