from collections import Counter
from datetime import datetime
from typing import List, Tuple, Dict
from ..domain import EnergyPattern, EnergyPersonality, PersonalityType

class PersonalityAnalyzer:
    """Creates personalities from patterns with improved weighted scoring"""
    
    def create_from_patterns(self, user_id: int, patterns: List[EnergyPattern]) -> EnergyPersonality:
        """Create personality from detected patterns"""
        
        if not patterns:
            return self._create_default_personality(user_id)
        
        # Get dominant patterns (top 3 by confidence)
        dominant_patterns = self._get_dominant_patterns(patterns)
        
        # Determine personality type based on weighted scoring
        personality_type = self._determine_personality_type(patterns)
        
        # Calculate score based on pattern confidences
        score = self._calculate_personality_score(patterns, personality_type)
        
        # Get more descriptive description
        description = self._generate_dynamic_description(patterns, personality_type)
        
        return EnergyPersonality(
            id=None,
            user_id=user_id,
            personality_type=personality_type,
            emoji=self._get_emoji(personality_type),
            score=score,
            description=description,
            dominant_patterns=dominant_patterns,
            detected_at=datetime.now()
        )
    
    def _get_dominant_patterns(self, patterns: List[EnergyPattern]) -> List[str]:
        """Get top 3 dominant patterns by confidence"""
        if not patterns:
            return []
        
        # Sort by confidence (descending)
        sorted_patterns = sorted(patterns, key=lambda p: p.confidence, reverse=True)
        return [p.pattern_type.value for p in sorted_patterns[:3]]
    
    def _determine_personality_type(self, patterns: List[EnergyPattern]) -> PersonalityType:
        """Determine personality based on weighted pattern scores"""
        
        if not patterns:
            return PersonalityType.BALANCED_USER
        
        # Weight patterns by confidence AND type importance
        personality_scores = self._calculate_personality_scores(patterns)
        
        # Get the highest scoring personality
        best_personality, best_score = max(personality_scores.items(), key=lambda x: x[1])
        
        # Check if we have a VERY strong single pattern (> 0.8 confidence)
        strongest_pattern = max(patterns, key=lambda p: p.confidence)
        if strongest_pattern.confidence >= 0.8:
            mapped = self._map_pattern_to_personality(strongest_pattern.pattern_type.value)
            # Only use if it's not Balanced (consistent_user maps to Balanced)
            if mapped != PersonalityType.BALANCED_USER:
                return mapped
        
        # Boost Balanced if consistent_user is very strong
        consistent_patterns = [p for p in patterns if p.pattern_type.value == "consistent_user"]
        if consistent_patterns and consistent_patterns[0].confidence >= 0.9:
            return PersonalityType.BALANCED_USER
        
        # Higher threshold for specific personalities
        if best_personality != PersonalityType.BALANCED_USER and best_score >= 0.7:
            return best_personality
        
        return PersonalityType.BALANCED_USER
    
    def _calculate_personality_scores(self, patterns: List[EnergyPattern]) -> Dict[PersonalityType, float]:
        """Calculate weighted scores for each possible personality"""
        scores = {
            PersonalityType.BALANCED_USER: 0.3,  # CHANGED: Higher base score from 0.25
            PersonalityType.NIGHT_OWL: 0.0,
            PersonalityType.EVENING_RELAXER: 0.0,
            PersonalityType.MORNING_ENERGIZER: 0.0,
            PersonalityType.DAYTIME_WORKER: 0.0,
            PersonalityType.WEEKDAY_WARRIOR: 0.0,
            PersonalityType.WEEKEND_HOST: 0.0,
            PersonalityType.ENERGY_MINIMALIST: 0.0,
            PersonalityType.ENERGY_ENTHUSIAST: 0.0,
        }
        
        # Pattern to personality mapping with weights
        # CHANGED: Reduced weights for specific patterns, increased for consumer types
        pattern_weights = {
            "night_owl": (PersonalityType.NIGHT_OWL, 0.8),        # Reduced from 1.0
            "evening_peaker": (PersonalityType.EVENING_RELAXER, 0.8),  # Reduced from 1.0
            "morning_bird": (PersonalityType.MORNING_ENERGIZER, 0.8),  # Reduced from 1.0
            "daytime_worker": (PersonalityType.DAYTIME_WORKER, 0.8),   # Reduced from 1.0
            "weekday_warrior": (PersonalityType.WEEKDAY_WARRIOR, 0.8), # Reduced from 1.0
            "weekend_spiker": (PersonalityType.WEEKEND_HOST, 0.8),     # Reduced from 1.0
            "consistent_user": (PersonalityType.BALANCED_USER, 0.7),   # CHANGED: Increased from 0.5
            "low_consumer": (PersonalityType.ENERGY_MINIMALIST, 1.0),  # CHANGED: Reduced from 1.2
            "high_consumer": (PersonalityType.ENERGY_ENTHUSIAST, 1.0), # CHANGED: Reduced from 1.2
        }
        
        # Add scores from each pattern
        for pattern in patterns:
            if pattern.pattern_type.value in pattern_weights:
                personality_type, weight = pattern_weights[pattern.pattern_type.value]
                scores[personality_type] += pattern.confidence * weight
        
        # CHANGED: REMOVED the penalty to Balanced User - this was causing the problem!
        # No longer penalizing Balanced when specific patterns exist
        
        # CHANGED: Additional boost for Balanced if consistent_user is present
        if "consistent_user" in [p.pattern_type.value for p in patterns]:
            # Find the consistent_user pattern confidence
            consistent_conf = next((p.confidence for p in patterns if p.pattern_type.value == "consistent_user"), 0)
            scores[PersonalityType.BALANCED_USER] += consistent_conf * 0.5  # Extra boost
        
        # CHANGED: Additional boost for Balanced if consumption patterns are present but weak
        consumption_patterns = ["low_consumer", "high_consumer"]
        consumption_in_patterns = any(p.pattern_type.value in consumption_patterns for p in patterns)
        
        if consumption_in_patterns:
            # Check if consumption patterns are weak (< 0.6 confidence)
            weak_consumption = True
            for pattern in patterns:
                if pattern.pattern_type.value in consumption_patterns and pattern.confidence >= 0.6:
                    weak_consumption = False
                    break
            
            if weak_consumption:
                scores[PersonalityType.BALANCED_USER] *= 1.3  # Boost Balanced for weak consumption patterns
        
        # Normalize scores to 0-1 range
        max_score = max(scores.values()) if scores else 1
        if max_score > 0:
            for key in scores:
                scores[key] = scores[key] / max_score
        
        return scores
    
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
            # If no directly relevant patterns, use average of all patterns
            avg_confidence = sum(p.confidence for p in patterns) / len(patterns)
        else:
            # Weighted average based on relevance
            weighted_sum = 0
            total_weight = 0
            for pattern in patterns:
                weight = 2.0 if self._is_pattern_relevant(pattern.pattern_type.value, personality_type) else 0.5
                weighted_sum += pattern.confidence * weight
                total_weight += weight
            
            avg_confidence = weighted_sum / total_weight if total_weight > 0 else 0.5
        
        # Convert to 0-100 scale
        base_score = avg_confidence * 100
        
        # CHANGED: More nuanced scoring adjustments
        if personality_type == PersonalityType.BALANCED_USER:
            # Boost Balanced scores slightly
            score = min(100, base_score * 1.05)
        elif avg_confidence > 0.8:
            # Strong patterns get small boost
            score = min(100, base_score * 1.05)
        elif avg_confidence < 0.4:
            # Very weak patterns get penalty
            score = base_score * 0.85
        elif avg_confidence < 0.6:
            # Moderate patterns stay as-is
            score = base_score * 0.95
        else:
            score = base_score
        
        return int(max(0, min(100, score)))  # Ensure 0-100 range
    
    def _generate_dynamic_description(self, patterns: List[EnergyPattern], 
                                    personality_type: PersonalityType) -> str:
        """Generate a more dynamic description based on actual patterns"""
        base_description = self._get_description(personality_type)
        
        if not patterns:
            return base_description
        
        # Get the top pattern relevant to this personality
        relevant_patterns = [p for p in patterns if self._is_pattern_relevant(p.pattern_type.value, personality_type)]
        
        if relevant_patterns:
            top_relevant = max(relevant_patterns, key=lambda p: p.confidence)
            top_confidence = top_relevant.confidence
        else:
            # If no directly relevant, use strongest pattern overall
            top_pattern = max(patterns, key=lambda p: p.confidence)
            top_confidence = top_pattern.confidence
        
        # CHANGED: Fixed the strength wording logic
        if top_confidence >= 0.8:
            strength = "strongly exhibits"
        elif top_confidence >= 0.6:
            strength = "clearly shows"
        elif top_confidence >= 0.4:
            strength = "tends to show"
        else:
            strength = "shows hints of"
        
        # Create enhanced description
        personality_descriptors = {
            PersonalityType.NIGHT_OWL: f"{strength} nighttime energy use",
            PersonalityType.EVENING_RELAXER: f"{strength} evening relaxation patterns",
            PersonalityType.MORNING_ENERGIZER: f"{strength} morning energy bursts",
            PersonalityType.DAYTIME_WORKER: f"{strength} daytime-focused energy use",
            PersonalityType.WEEKDAY_WARRIOR: f"{strength} weekday energy patterns",
            PersonalityType.WEEKEND_HOST: f"{strength} weekend energy spikes",
            PersonalityType.ENERGY_MINIMALIST: f"{strength} energy-efficient habits",
            PersonalityType.ENERGY_ENTHUSIAST: f"{strength} generous energy use",
            PersonalityType.BALANCED_USER: f"with {strength.replace('exhibits', 'displayed').replace('shows', 'displayed')} consistency",  # Special case for Balanced
        }
        
        if personality_type in personality_descriptors:
            if personality_type == PersonalityType.BALANCED_USER:
                return f"{base_description} ({personality_descriptors[personality_type]})"
            else:
                return f"{base_description} (You {personality_descriptors[personality_type]})"
        
        return base_description
    
    def _is_pattern_relevant(self, pattern_type: str, 
                           personality_type: PersonalityType) -> bool:
        """Check if pattern is relevant to personality"""
        relevance_map = {
            PersonalityType.NIGHT_OWL: ["night_owl"],
            PersonalityType.EVENING_RELAXER: ["evening_peaker"],
            PersonalityType.MORNING_ENERGIZER: ["morning_bird"],
            PersonalityType.DAYTIME_WORKER: ["daytime_worker"],
            PersonalityType.WEEKDAY_WARRIOR: ["weekday_warrior"],
            PersonalityType.WEEKEND_HOST: ["weekend_spiker"],
            PersonalityType.ENERGY_MINIMALIST: ["low_consumer"],  # CHANGED: Removed consistent_user
            PersonalityType.ENERGY_ENTHUSIAST: ["high_consumer"],
            PersonalityType.BALANCED_USER: ["consistent_user"],  # CHANGED: Added for Balanced
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