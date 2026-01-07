# Dependency injection setup
from fastapi import Depends
from sqlalchemy.orm import Session

from infra.db import get_db
from modules.pattern.services.pattern_analyzer import PatternAnalyzer
from modules.pattern.services.personality_analyzer import PersonalityAnalyzer
from infra.pattern.repository import (
    SQLAlchemyPatternRepository, 
    SQLAlchemyPersonalityRepository
)
from modules.pattern.use_cases import AnalyzePatterns, GetUserPatterns, GetUserPersonality

def get_pattern_repository(db: Session = Depends(get_db)):
    return SQLAlchemyPatternRepository(db)

def get_personality_repository(db: Session = Depends(get_db)):
    return SQLAlchemyPersonalityRepository(db)

def get_pattern_analyzer_service():
    return PatternAnalyzer()

def get_personality_analyzer_service():
    return PersonalityAnalyzer()

def get_analyze_patterns_use_case(
    pattern_repo: SQLAlchemyPatternRepository = Depends(get_pattern_repository),
    personality_repo: SQLAlchemyPersonalityRepository = Depends(get_personality_repository),
    pattern_analyzer: PatternAnalyzer = Depends(get_pattern_analyzer_service),
    personality_analyzer: PersonalityAnalyzer = Depends(get_personality_analyzer_service)
) -> AnalyzePatterns:
    return AnalyzePatterns(pattern_repo, personality_repo, pattern_analyzer, personality_analyzer)

def get_get_patterns_use_case(
    pattern_repo: SQLAlchemyPatternRepository = Depends(get_pattern_repository)
) -> GetUserPatterns:
    return GetUserPatterns(pattern_repo)

def get_get_personality_use_case(
    personality_repo: SQLAlchemyPersonalityRepository = Depends(get_personality_repository)
) -> GetUserPersonality:
    return GetUserPersonality(personality_repo)