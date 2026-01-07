# DTOs - API boundaries
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from modules.pattern.domain import EnergyPattern, EnergyPersonality

class PatternAnalysisRequestDTO(BaseModel):
    """Input for pattern analysis"""
    user_id: int
    days: int = Field(default=30, ge=7, le=90)
    
    @validator('days')
    def validate_days(cls, v):
        if v < 7:
            raise ValueError("Need at least 7 days of data")
        return v

class PatternDTO(BaseModel):
    """Output pattern DTO"""
    id: Optional[int] = None
    pattern_type: str
    confidence: float
    description: str
    detected_at: datetime
    priority: str
    
    class Config:
        from_attributes = True

class PersonalityDTO(BaseModel):
    """Output personality DTO"""
    personality_type: str
    emoji: str
    score: int
    description: str
    dominant_patterns: List[str]
    detected_at: datetime
    display_name: str
    
    class Config:
        from_attributes = True

class PatternAnalysisResultDTO(BaseModel):
    """Complete analysis result"""
    user_id: int
    analysis_date: datetime
    patterns: List[PatternDTO]
    personality: PersonalityDTO
    summary: str
    
    @classmethod
    def from_domain(cls, user_id: int, patterns: List[EnergyPattern], personality: EnergyPersonality):
        return cls(
            user_id=user_id,
            analysis_date=datetime.now(),
            patterns=[
                PatternDTO(
                    id=p.id,
                    pattern_type=p.pattern_type.value,
                    confidence=p.confidence,
                    description=p.description,
                    detected_at=p.detected_at,
                    priority=p.priority
                )
                for p in patterns
            ],
            personality=PersonalityDTO(
                personality_type=personality.personality_type.value,
                emoji=personality.emoji,
                score=personality.score,
                description=personality.description,
                dominant_patterns=personality.dominant_patterns,
                detected_at=personality.detected_at,
                display_name=personality.display_name
            ),
            summary=f"Analyzed {len(patterns)} patterns"
        )