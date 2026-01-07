# Pattern detection service
import pandas as pd
from datetime import datetime, date
from typing import List, Tuple
from core.settings import settings
from ..domain import EnergyPattern, PatternType

class PatternAnalyzer:
    """Service for detecting patterns from raw data"""
    
    def analyze_consumption(self, data: List[Tuple[datetime, float]], 
                          user_id: int, start_date: date, end_date: date) -> List[EnergyPattern]:
        """Detect patterns from consumption data"""
        patterns = []
        
        if not data or len(data) < 24:
            return patterns
        
        df = pd.DataFrame(data, columns=['datetime', 'kwh'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df['hour'] = df['datetime'].dt.hour
        
        # Night owl pattern (hard + soft thresholds)
        night_percentage = self._calculate_night_percentage(df)
        # Hard trigger
        if night_percentage >= settings.pattern_night_threshold:
            patterns.append(EnergyPattern(
                id=None,
                user_id=user_id,
                pattern_type=PatternType.NIGHT_OWL,
                confidence=min(0.95, night_percentage * 1.5),
                description=f"Night owl - {night_percentage:.0%} of energy used at night",
                detected_at=datetime.now(),
                start_date=start_date,
                end_date=end_date
            ))
        # Soft (near-threshold) trigger: lower confidence, flagged as 'possible'
        elif night_percentage >= settings.pattern_night_soft_threshold:
            soft_conf = min(0.6, night_percentage * 1.25)
            patterns.append(EnergyPattern(
                id=None,
                user_id=user_id,
                pattern_type=PatternType.NIGHT_OWL,
                confidence=soft_conf,
                description=f"Possible night owl (near threshold) - {night_percentage:.0%} of energy used at night",
                detected_at=datetime.now(),
                start_date=start_date,
                end_date=end_date
            ))
        
        # Weekday warrior pattern (need at least 7 days)
        if df['datetime'].dt.date.nunique() >= 7:
            weekday_ratio = self._calculate_weekday_ratio(df)
            # Hard trigger
            if weekday_ratio >= settings.pattern_weekday_ratio_threshold:
                patterns.append(EnergyPattern(
                    id=None,
                    user_id=user_id,
                    pattern_type=PatternType.WEEKDAY_WARRIOR,
                    confidence=min(0.9, (weekday_ratio - 1) / 2),
                    description=f"Weekday warrior - {weekday_ratio:.1f}x more on weekdays",
                    detected_at=datetime.now(),
                    start_date=start_date,
                    end_date=end_date
                ))
            # Soft trigger
            elif weekday_ratio >= settings.pattern_weekday_soft_ratio:
                soft_conf = min(0.6, (weekday_ratio - 1) / 1.5)
                patterns.append(EnergyPattern(
                    id=None,
                    user_id=user_id,
                    pattern_type=PatternType.WEEKDAY_WARRIOR,
                    confidence=soft_conf,
                    description=f"Possible weekday warrior (near threshold) - {weekday_ratio:.2f}x more on weekdays",
                    detected_at=datetime.now(),
                    start_date=start_date,
                    end_date=end_date
                ))
        
        return patterns
    
    def _calculate_night_percentage(self, df: pd.DataFrame) -> float:
        """Calculate percentage of usage at night (10 PM - 6 AM)"""
        night_mask = (df['hour'] >= 22) | (df['hour'] < 6)
        night_kwh = df[night_mask]['kwh'].sum()
        total_kwh = df['kwh'].sum()
        return night_kwh / total_kwh if total_kwh > 0 else 0
    
    def _calculate_weekday_ratio(self, df: pd.DataFrame) -> float:
        """Calculate weekday to weekend ratio"""
        df['is_weekend'] = df['datetime'].dt.dayofweek >= 5
        weekday_avg = df[~df['is_weekend']]['kwh'].mean()
        weekend_avg = df[df['is_weekend']]['kwh'].mean()
        return weekday_avg / weekend_avg if weekend_avg > 0 else 1