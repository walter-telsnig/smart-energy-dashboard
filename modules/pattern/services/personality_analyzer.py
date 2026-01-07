# Personality creation service
from collections import Counter
from datetime import datetime
from typing import List
from ..domain import EnergyPattern, EnergyPersonality, PersonalityType

class PersonalityAnalyzer:
    """Service for creating personality from patterns"""
    
    def create_from_patterns(self, user_id: int, patterns: List[EnergyPattern]) -> EnergyPersonality:
        """Create personality entity from detected patterns"""
        
        if not patterns:
            return self._create_default_personality(user_id)
        
        # Filter high confidence patterns
        high_conf_patterns = [p for p in patterns if p.confidence >= 0.7]
        
        if not high_conf_patterns:
            return self._create_balanced_personality(user_id, patterns)
        
        # Find dominant patterns
        pattern_counter = Counter([p.pattern_type.value for p in high_conf_patterns])
        dominant_patterns = [pt for pt, _ in pattern_counter.most_common(3)]
        
        # Determine personality type
        personality_type = self._determine_personality_type(dominant_patterns)
        
        # Calculate score
        score = self._calculate_score(high_conf_patterns, dominant_patterns)
        
        return EnergyPersonality(
            id=None,
            user_id=user_id,
            personality_type=personality_type,
            emoji=self._get_emoji(personality_type),
            score=score,
            description=self._get_description(personality_type),
            dominant_patterns=dominant_patterns,
            detected_at=datetime.now()
        )
    
    def _determine_personality_type(self, dominant_patterns: List[str]) -> PersonalityType:
        if not dominant_patterns:
            return PersonalityType.BALANCED_USER
        
        primary_pattern = dominant_patterns[0]
        
        mapping = {
            "night_owl": PersonalityType.NIGHT_OWL,
            "weekday_warrior": PersonalityType.WEEKDAY_WARRIOR,
            "morning_bird": PersonalityType.MORNING_ENERGIZER,
            "solar_aligned": PersonalityType.SOLAR_OPTIMIZER,
        }
        
        return mapping.get(primary_pattern, PersonalityType.BALANCED_USER)
    
    def _calculate_score(self, patterns: List[EnergyPattern], 
                        dominant_patterns: List[str]) -> int:
        if not patterns:
            return 50
        
        relevant = [p for p in patterns if p.pattern_type.value in dominant_patterns]
        
        if not relevant:
            return 50
        
        avg_confidence = sum(p.confidence for p in relevant) / len(relevant)
        return int(avg_confidence * 100)
    
    def _get_emoji(self, personality_type: PersonalityType) -> str:
        return {
            PersonalityType.BALANCED_USER: "⚖️",
            PersonalityType.NIGHT_OWL: "🦉",
            PersonalityType.WEEKDAY_WARRIOR: "💼",
            PersonalityType.MORNING_ENERGIZER: "🌅",
            PersonalityType.SOLAR_OPTIMIZER: "☀️",
        }.get(personality_type, "👤")
    
    def _get_description(self, personality_type: PersonalityType) -> str:
        return {
            PersonalityType.BALANCED_USER: "Your energy usage is well-distributed",
            PersonalityType.NIGHT_OWL: "You're most active when others sleep",
            PersonalityType.WEEKDAY_WARRIOR: "Your energy spikes during the work week",
            PersonalityType.MORNING_ENERGIZER: "You start your day with high energy",
            PersonalityType.SOLAR_OPTIMIZER: "You naturally align with solar production",
        }.get(personality_type, "Energy user")
    
    def _create_default_personality(self, user_id: int) -> EnergyPersonality:
        return EnergyPersonality(
            id=None,
            user_id=user_id,
            personality_type=PersonalityType.BALANCED_USER,
            emoji="⚖️",
            score=50,
            description="Insufficient data for analysis",
            dominant_patterns=[],
            detected_at=datetime.now()
        )
    
    def _create_balanced_personality(self, user_id: int, 
                                   patterns: List[EnergyPattern]) -> EnergyPersonality:
        return EnergyPersonality(
            id=None,
            user_id=user_id,
            personality_type=PersonalityType.BALANCED_USER,
            emoji="⚖️",
            score=50,
            description="Balanced energy usage",
            dominant_patterns=[p.pattern_type.value for p in patterns[:3]],
            detected_at=datetime.now()
        )