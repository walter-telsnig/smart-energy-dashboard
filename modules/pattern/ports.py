# Ports/interfaces - dependency inversion
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Optional, List, Tuple
from .domain import EnergyPattern, EnergyPersonality

class PatternRepositoryPort(ABC):
    """Port for pattern data access"""
    
    @abstractmethod
    def create_pattern(self, pattern: EnergyPattern) -> EnergyPattern:
        pass
    
    @abstractmethod
    def get_user_patterns(self, user_id: int, limit: int = 100, offset: int = 0) -> List[EnergyPattern]:
        pass
    
    @abstractmethod
    def get_consumption_data(self, user_id: int, start_date: date, end_date: date) -> List[Tuple[datetime, float]]:
        pass
    
    @abstractmethod
    def get_pv_data(self, user_id: int, start_date: date, end_date: date) -> List[Tuple[datetime, float]]:
        pass

class PersonalityRepositoryPort(ABC):
    """Port for personality data access"""
    
    @abstractmethod
    def save_personality(self, personality: EnergyPersonality) -> EnergyPersonality:
        pass
    
    @abstractmethod
    def get_personality(self, user_id: int) -> Optional[EnergyPersonality]:
        pass
