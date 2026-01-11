from unittest.mock import MagicMock
from modules.pattern.use_cases import AnalyzePatterns
from modules.pattern.dto import PatternAnalysisRequestDTO
from modules.pattern.domain import EnergyPattern, PatternType, EnergyPersonality, PersonalityType
from datetime import datetime, date


def make_pattern():
    return EnergyPattern(
        id=None,
        user_id=1,
        pattern_type=PatternType.NIGHT_OWL,
        confidence=0.8,
        description="",
        detected_at=datetime.now(),
        start_date=date.today(),
        end_date=date.today()
    )


def test_analyze_patterns_orchestration_calls_repos_and_analyzers():
    pattern_repo = MagicMock()
    personality_repo = MagicMock()
    pattern_repo.get_consumption_data.return_value = [(datetime.now(), 1.0)] * 24 * 7

    analyzer = MagicMock()
    analyzer.analyze_consumption.return_value = [make_pattern()]

    # Return a concrete EnergyPersonality so DTO conversion works
    personality = EnergyPersonality(
        id=None,
        user_id=1,
        personality_type=PersonalityType.NIGHT_OWL,
        emoji="🦉",
        score=80,
        description="x",
        dominant_patterns=["night_owl"],
        detected_at=datetime.now()
    )

    personality_analyzer = MagicMock()
    personality_analyzer.create_from_patterns.return_value = personality

    # Personality repo should return the saved personality (not a MagicMock)
    personality_repo.save_personality.return_value = personality

    # Ensure create_pattern returns the passed object (simulate db flush id assignment)
    pattern_repo.create_pattern.side_effect = lambda p: p

    uc = AnalyzePatterns(pattern_repo, personality_repo, analyzer, personality_analyzer)
    dto = PatternAnalysisRequestDTO(user_id=1, days=7)
    result = uc(dto)

    analyzer.analyze_consumption.assert_called_once()
    personality_analyzer.create_from_patterns.assert_called_once()
    pattern_repo.create_pattern.assert_called()
    personality_repo.save_personality.assert_called()
    assert result.user_id == dto.user_id
