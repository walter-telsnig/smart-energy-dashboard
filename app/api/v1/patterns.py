# FastAPI endpoints
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from infra.db import get_db
from modules.pattern.use_cases import AnalyzePatterns, GetUserPatterns, GetUserPersonality
from modules.pattern.services.pattern_analyzer import PatternAnalyzer
from modules.pattern.services.personality_analyzer import PersonalityAnalyzer
from infra.pattern.repository import (
    SQLAlchemyPatternRepository, 
    SQLAlchemyPersonalityRepository
)
from modules.pattern.dto import (
    PatternAnalysisRequestDTO, 
    PatternAnalysisResultDTO, 
    PatternDTO,
    PersonalityDTO
)

router = APIRouter(prefix="/patterns", tags=["patterns"])

# Dependency injection
def get_pattern_repo(db: Session = Depends(get_db)):
    return SQLAlchemyPatternRepository(db)

def get_personality_repo(db: Session = Depends(get_db)):
    return SQLAlchemyPersonalityRepository(db)

def get_pattern_analyzer():
    return PatternAnalyzer()

def get_personality_analyzer():
    return PersonalityAnalyzer()

def get_analyze_patterns_use_case(
    pattern_repo: SQLAlchemyPatternRepository = Depends(get_pattern_repo),
    personality_repo: SQLAlchemyPersonalityRepository = Depends(get_personality_repo),
    pattern_analyzer: PatternAnalyzer = Depends(get_pattern_analyzer),
    personality_analyzer: PersonalityAnalyzer = Depends(get_personality_analyzer)
):
    return AnalyzePatterns(pattern_repo, personality_repo, pattern_analyzer, personality_analyzer)

def get_get_patterns_use_case(
    pattern_repo: SQLAlchemyPatternRepository = Depends(get_pattern_repo)
):
    return GetUserPatterns(pattern_repo)

def get_get_personality_use_case(
    personality_repo: SQLAlchemyPersonalityRepository = Depends(get_personality_repo)
):
    return GetUserPersonality(personality_repo)

# Endpoints
@router.post("/analyze", response_model=PatternAnalysisResultDTO)
async def analyze_patterns(
    request: PatternAnalysisRequestDTO,
    use_case: AnalyzePatterns = Depends(get_analyze_patterns_use_case)
):
    """Analyze energy patterns for a user"""
    try:
        return use_case(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/{user_id}/patterns", response_model=List[PatternDTO])
async def get_user_patterns(
    user_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    use_case: GetUserPatterns = Depends(get_get_patterns_use_case)
):
    """Get patterns for a user"""
    try:
        patterns = use_case(user_id, limit, offset)
        return [
            PatternDTO(
                id=p.id,
                pattern_type=p.pattern_type.value,
                confidence=p.confidence,
                description=p.description,
                detected_at=p.detected_at,
                priority=p.priority
            )
            for p in patterns
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patterns: {str(e)}")

@router.get("/{user_id}/personality", response_model=PersonalityDTO)
async def get_user_personality(
    user_id: int,
    use_case: GetUserPersonality = Depends(get_get_personality_use_case)
):
    """Get user's energy personality"""
    try:
        personality = use_case(user_id)
        if not personality:
            raise HTTPException(status_code=404, detail="Personality not found")
        
        return PersonalityDTO(
            personality_type=personality.personality_type.value,
            emoji=personality.emoji,
            score=personality.score,
            description=personality.description,
            dominant_patterns=personality.dominant_patterns,
            detected_at=personality.detected_at,
            display_name=personality.display_name
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get personality: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "pattern-analysis",
        "timestamp": datetime.now().isoformat()
    }