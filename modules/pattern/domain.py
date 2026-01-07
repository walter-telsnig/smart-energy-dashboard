# Pure domain entities - NO complex logic, NO dependencies
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

class PatternType(str, Enum):
    NIGHT_OWL = "night_owl"
    WEEKDAY_WARRIOR = "weekday_warrior"
    MORNING_BIRD = "morning_bird"
    CONSISTENT_USER = "consistent_user"
    SOLAR_ALIGNED = "solar_aligned"
    SOLAR_MISALIGNED = "solar_misaligned"

@dataclass(frozen=True)
class EnergyPattern:
    """Domain entity - only data + validation"""
    id: Optional[int]
    user_id: int
    pattern_type: PatternType
    confidence: float  # 0.0 to 1.0
    description: str
    detected_at: datetime
    start_date: date
    end_date: date
    
    def __post_init__(self):
        """Only invariants"""
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        if self.start_date > self.end_date:
            raise ValueError("Start date must be before end date")
    
    @property
    def priority(self) -> str:
        """Simple derived property - not complex logic"""
        if self.confidence >= 0.8:
            return "high"
        elif self.confidence >= 0.6:
            return "medium"
        return "low"

class PersonalityType(str, Enum):
    BALANCED_USER = "balanced_user"
    NIGHT_OWL = "night_owl"
    WEEKDAY_WARRIOR = "weekday_warrior"
    MORNING_ENERGIZER = "morning_energizer"
    SOLAR_OPTIMIZER = "solar_optimizer"
    UNPREDICTABLE = "unpredictable"

@dataclass(frozen=True)
class EnergyPersonality:
    """Domain entity - only data + validation"""
    id: Optional[int]
    user_id: int
    personality_type: PersonalityType
    emoji: str
    score: int  # 0-100
    description: str
    dominant_patterns: List[str]
    detected_at: datetime
    
    def __post_init__(self):
        """Only invariants"""
        if not 0 <= self.score <= 100:
            raise ValueError("Score must be between 0 and 100")
        if not self.emoji:
            raise ValueError("Emoji is required")
    
    @property
    def display_name(self) -> str:
        """Simple string formatting"""
        return f"{self.emoji} {self.personality_type.value.replace('_', ' ').title()}"