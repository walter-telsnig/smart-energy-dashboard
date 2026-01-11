# Use cases - orchestration layer
from datetime import date, timedelta
from typing import List, Optional

from .ports import PatternRepositoryPort, PersonalityRepositoryPort
from .services.pattern_analyzer import PatternAnalyzer
from .services.personality_analyzer import PersonalityAnalyzer
from .domain import EnergyPattern, EnergyPersonality
from .dto import PatternAnalysisRequestDTO, PatternAnalysisResultDTO

class AnalyzePatterns:
    """Orchestrates pattern analysis"""
    
    def __init__(self, 
                 pattern_repo: PatternRepositoryPort,
                 personality_repo: PersonalityRepositoryPort,
                 pattern_analyzer: PatternAnalyzer,
                 personality_analyzer: PersonalityAnalyzer):
        self.pattern_repo = pattern_repo
        self.personality_repo = personality_repo
        self.pattern_analyzer = pattern_analyzer
        self.personality_analyzer = personality_analyzer
    
    def __call__(self, dto: PatternAnalysisRequestDTO) -> PatternAnalysisResultDTO:
        # 1. Get date range
        end_date = date.today()
        start_date = end_date - timedelta(days=dto.days)
        
        # 2. Get consumption data
        consumption_data = self.pattern_repo.get_consumption_data(
            dto.user_id, start_date, end_date
        )
        
        if not consumption_data:
            raise ValueError(f"No consumption data for user {dto.user_id}")
        
        # 3. Analyze patterns
        patterns = self.pattern_analyzer.analyze_consumption(
            consumption_data, dto.user_id, start_date, end_date
        )
        
        # 4. Create personality
        personality = self.personality_analyzer.create_from_patterns(
            dto.user_id, patterns
        )
        
        # 5. Persist
        saved_patterns = [self.pattern_repo.create_pattern(p) for p in patterns]
        saved_personality = self.personality_repo.save_personality(personality)
        
        # 6. Return DTO
        return PatternAnalysisResultDTO.from_domain(
            dto.user_id, saved_patterns, saved_personality
        )

class GetUserPatterns:
    """Get user's patterns"""
    
    def __init__(self, repo: PatternRepositoryPort):
        self.repo = repo
    
    def __call__(self, user_id: int, limit: int = 100, offset: int = 0) -> List[EnergyPattern]:
        return self.repo.get_user_patterns(user_id, limit, offset)

class GetUserPersonality:
    """Get user's personality"""
    
    def __init__(self, repo: PersonalityRepositoryPort):
        self.repo = repo
    
    def __call__(self, user_id: int) -> Optional[EnergyPersonality]:
        return self.repo.get_personality(user_id)