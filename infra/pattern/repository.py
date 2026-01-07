# SQLAlchemy implementations
from datetime import datetime, timedelta, date
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from modules.pattern.ports import PatternRepositoryPort, PersonalityRepositoryPort
from modules.pattern.domain import EnergyPattern, PatternType, EnergyPersonality, PersonalityType
from modules.pattern.model import Pattern, EnergyPersonality as PersonalityModel
from infra.models import Consumption, PV

class SQLAlchemyPatternRepository(PatternRepositoryPort):
    def __init__(self, session: Session):
        self.session = session
    
    def create_pattern(self, pattern: EnergyPattern) -> EnergyPattern:
        model = Pattern(
            user_id=pattern.user_id,
            pattern_type=pattern.pattern_type.value,
            confidence=pattern.confidence,
            description=pattern.description,
            detected_at=pattern.detected_at,
            start_date=pattern.start_date,
            end_date=pattern.end_date
        )
        
        self.session.add(model)
        self.session.flush()
        
        return EnergyPattern(
            id=model.id,
            user_id=model.user_id,
            pattern_type=PatternType(model.pattern_type),
            confidence=model.confidence,
            description=model.description,
            detected_at=model.detected_at,
            start_date=model.start_date,
            end_date=model.end_date
        )
    
    def get_user_patterns(self, user_id: int, limit: int = 100, offset: int = 0) -> List[EnergyPattern]:
        models = self.session.query(Pattern).filter(
            Pattern.user_id == user_id
        ).order_by(Pattern.detected_at.desc()).limit(limit).offset(offset).all()
        
        return [
            EnergyPattern(
                id=m.id,
                user_id=m.user_id,
                pattern_type=PatternType(m.pattern_type),
                confidence=m.confidence,
                description=m.description,
                detected_at=m.detected_at,
                start_date=m.start_date,
                end_date=m.end_date
            )
            for m in models
        ]
    
    def get_consumption_data(self, user_id: int, start_date: date, end_date: date) -> List[Tuple[datetime, float]]:
        query = self.session.query(
            Consumption.datetime,
            Consumption.consumption_kwh
        ).filter(
            Consumption.datetime >= datetime.combine(start_date, datetime.min.time()),
            Consumption.datetime <= datetime.combine(end_date, datetime.max.time())
        ).order_by(Consumption.datetime)
        
        return [(row.datetime, row.consumption_kwh) for row in query.all()]
    
    def get_pv_data(self, user_id: int, start_date: date, end_date: date) -> List[Tuple[datetime, float]]:
        query = self.session.query(
            PV.datetime,
            PV.production_kw
        ).filter(
            PV.datetime >= datetime.combine(start_date, datetime.min.time()),
            PV.datetime <= datetime.combine(end_date, datetime.max.time())
        ).order_by(PV.datetime)
        
        return [(row.datetime, row.production_kw) for row in query.all()]

class SQLAlchemyPersonalityRepository(PersonalityRepositoryPort):
    def __init__(self, session: Session):
        self.session = session
    
    def save_personality(self, personality: EnergyPersonality) -> EnergyPersonality:
        existing = self.session.query(PersonalityModel).filter(
            PersonalityModel.user_id == personality.user_id
        ).first()
        
        if existing:
            existing.personality_type = personality.personality_type.value
            existing.emoji = personality.emoji
            existing.score = personality.score
            existing.description = personality.description
            existing.dominant_patterns = personality.dominant_patterns
            existing.detected_at = personality.detected_at
            model = existing
        else:
            model = PersonalityModel(
                user_id=personality.user_id,
                personality_type=personality.personality_type.value,
                emoji=personality.emoji,
                score=personality.score,
                description=personality.description,
                dominant_patterns=personality.dominant_patterns,
                detected_at=personality.detected_at
            )
            self.session.add(model)
        
        self.session.flush()
        
        return EnergyPersonality(
            id=model.id,
            user_id=model.user_id,
            personality_type=PersonalityType(model.personality_type),
            emoji=model.emoji,
            score=model.score,
            description=model.description,
            dominant_patterns=model.dominant_patterns,
            detected_at=model.detected_at
        )
    
    def get_personality(self, user_id: int) -> Optional[EnergyPersonality]:
        model = self.session.query(PersonalityModel).filter(
            PersonalityModel.user_id == user_id
        ).first()
        
        if not model:
            return None
        
        return EnergyPersonality(
            id=model.id,
            user_id=model.user_id,
            personality_type=PersonalityType(model.personality_type),
            emoji=model.emoji,
            score=model.score,
            description=model.description,
            dominant_patterns=model.dominant_patterns,
            detected_at=model.detected_at
        )