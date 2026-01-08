from collections import Counter
from datetime import datetime
from typing import List
from ..domain import EnergyPattern, EnergyPersonality, PersonalityType

class PersonalityAnalyzer:
    """Creates personalities from patterns with better mapping"""
    
    def create_from_patterns(self, user_id: int, patterns: List[EnergyPattern]) -> EnergyPersonality:
        """Create personality from detected patterns"""
        
        if not patterns:
            return self._create_default_personality(user_id)
        
        # Group patterns by type and count
        pattern_counts = Counter([p.pattern_type.value for p in patterns])
        
        # Get dominant patterns (top 3 by count, then confidence)
        dominant_patterns = self._get_dominant_patterns(patterns)
        
        # Determine personality type based on pattern combination
        personality_type = self._determine_personality_type(pattern_counts, patterns)
        
        # Calculate score based on pattern confidences
        score = self._calculate_personality_score(patterns, personality_type)
        
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
    
    def _get_dominant_patterns(self, patterns: List[EnergyPattern]) -> List[str]:
        """Get top 3 dominant patterns"""
        if not patterns:
            return []
        
        # Sort by confidence
        sorted_patterns = sorted(patterns, key=lambda p: p.confidence, reverse=True)
        return [p.pattern_type.value for p in sorted_patterns[:3]]
    
    def _determine_personality_type(self, pattern_counts: Counter, 
                                   patterns: List[EnergyPattern]) -> PersonalityType:
        """Determine personality based on pattern combination"""
        
        # Check for specific pattern combinations
        if pattern_counts.get("night_owl", 0) > 0:
            return PersonalityType.NIGHT_OWL
        
        if pattern_counts.get("evening_peaker", 0) > 0:
            return PersonalityType.EVENING_RELAXER
        
        if pattern_counts.get("morning_bird", 0) > 0:
            return PersonalityType.MORNING_ENERGIZER
        
        if pattern_counts.get("weekday_warrior", 0) > 0:
            return PersonalityType.WEEKDAY_WARRIOR
        
        if pattern_counts.get("weekend_spiker", 0) > 0:
            return PersonalityType.WEEKEND_HOST
        
        if pattern_counts.get("daytime_worker", 0) > 0:
            return PersonalityType.DAYTIME_WORKER
        
        if pattern_counts.get("solar_aligned", 0) > 0:
            return PersonalityType.SOLAR_OPTIMIZER
        
        # Check for consumer type
        if pattern_counts.get("low_consumer", 0) > 0:
            return PersonalityType.ENERGY_MINIMALIST
        
        if pattern_counts.get("high_consumer", 0) > 0:
            return PersonalityType.ENERGY_ENTHUSIAST
        
        # Default based on confidence
        if patterns:
            highest_conf = max(patterns, key=lambda p: p.confidence)
            return self._map_pattern_to_personality(highest_conf.pattern_type.value)
        
        return PersonalityType.BALANCED_USER
    
    def _map_pattern_to_personality(self, pattern_type: str) -> PersonalityType:
        """Map pattern to personality"""
        mapping = {
            "night_owl": PersonalityType.NIGHT_OWL,
            "evening_peaker": PersonalityType.EVENING_RELAXER,
            "morning_bird": PersonalityType.MORNING_ENERGIZER,
            "weekday_warrior": PersonalityType.WEEKDAY_WARRIOR,
            "weekend_spiker": PersonalityType.WEEKEND_HOST,
            "daytime_worker": PersonalityType.DAYTIME_WORKER,
            "consistent_user": PersonalityType.BALANCED_USER,
            "low_consumer": PersonalityType.ENERGY_MINIMALIST,
            "high_consumer": PersonalityType.ENERGY_ENTHUSIAST,
        }
        return mapping.get(pattern_type, PersonalityType.BALANCED_USER)
    
    def _calculate_personality_score(self, patterns: List[EnergyPattern], 
                                   personality_type: PersonalityType) -> int:
        """Calculate personality score (0-100)"""
        if not patterns:
            return 50
        
        # Get patterns relevant to this personality
        relevant_patterns = [
            p for p in patterns 
            if self._is_pattern_relevant(p.pattern_type.value, personality_type)
        ]
        
        if not relevant_patterns:
            return 50
        
        # Average confidence of relevant patterns
        avg_confidence = sum(p.confidence for p in relevant_patterns) / len(relevant_patterns)
        return int(avg_confidence * 100)
    
    def _is_pattern_relevant(self, pattern_type: str, 
                           personality_type: PersonalityType) -> bool:
        """Check if pattern is relevant to personality"""
        relevance_map = {
            PersonalityType.NIGHT_OWL: ["night_owl", "late_evening"],
            PersonalityType.EVENING_RELAXER: ["evening_peaker", "dinner_peak"],
            PersonalityType.MORNING_ENERGIZER: ["morning_bird", "morning_rush"],
            PersonalityType.WEEKDAY_WARRIOR: ["weekday_warrior", "daytime_worker"],
            PersonalityType.WEEKEND_HOST: ["weekend_spiker"],
            PersonalityType.ENERGY_MINIMALIST: ["low_consumer", "consistent_user"],
            PersonalityType.ENERGY_ENTHUSIAST: ["high_consumer", "variable_user"],
        }
        return pattern_type in relevance_map.get(personality_type, [])
    
    def _get_emoji(self, personality_type: PersonalityType) -> str:
        """Get emoji for personality type"""
        emojis = {
            PersonalityType.BALANCED_USER: "⚖️",
            PersonalityType.NIGHT_OWL: "🦉",
            PersonalityType.MORNING_ENERGIZER: "🌅",
            PersonalityType.DAYTIME_WORKER: "💼",
            PersonalityType.EVENING_RELAXER: "🌙",
            PersonalityType.WEEKDAY_WARRIOR: "📅",
            PersonalityType.WEEKEND_HOST: "🎉",
            PersonalityType.SOLAR_OPTIMIZER: "☀️",
            PersonalityType.ENERGY_MINIMALIST: "🌿",
            PersonalityType.ENERGY_ENTHUSIAST: "⚡",
            PersonalityType.UNPREDICTABLE: "🎲"
        }
        return emojis.get(personality_type, "👤")
    
    def _get_description(self, personality_type: PersonalityType) -> str:
        """Get description for personality type"""
        descriptions = {
            PersonalityType.BALANCED_USER: "Your energy usage is well-distributed throughout the day",
            PersonalityType.NIGHT_OWL: "You're most active when others sleep - night is your peak time",
            PersonalityType.MORNING_ENERGIZER: "You start your day with high energy activity",
            PersonalityType.DAYTIME_WORKER: "Your energy peaks align with traditional 9-5 work hours",
            PersonalityType.EVENING_RELAXER: "You unwind in the evening with increased energy use",
            PersonalityType.WEEKDAY_WARRIOR: "Your energy use spikes during the work week",
            PersonalityType.WEEKEND_HOST: "Weekends are when your home comes alive with energy",
            PersonalityType.SOLAR_OPTIMIZER: "You naturally align energy use with solar production",
            PersonalityType.ENERGY_MINIMALIST: "You use energy very efficiently and intentionally",
            PersonalityType.ENERGY_ENTHUSIAST: "You're not afraid to use energy when you need it",
            PersonalityType.UNPREDICTABLE: "Your energy patterns keep us guessing!"
        }
        return descriptions.get(personality_type, "Energy user")
    
    def _create_default_personality(self, user_id: int) -> EnergyPersonality:
        """Create default personality"""
        return EnergyPersonality(
            id=None,
            user_id=user_id,
            personality_type=PersonalityType.BALANCED_USER,
            emoji="⚖️",
            score=50,
            description="Analysis in progress - check back soon",
            dominant_patterns=[],
            detected_at=datetime.now()
        )