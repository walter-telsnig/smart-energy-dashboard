import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import List, Tuple
from ..domain import EnergyPattern, PatternType

class PatternAnalyzer:
    """Enhanced pattern detector with more patterns and adjusted thresholds"""
    
    def analyze_consumption(self, data: List[Tuple[datetime, float]], 
                          user_id: int, start_date: date, end_date: date) -> List[EnergyPattern]:
        """Detect multiple energy usage patterns"""
        patterns = []
        
        if len(data) < 24:  # Need at least 24 hours
            return patterns
        
        df = self._prepare_dataframe(data)
        
        # 1. NIGHT OWL (lowered threshold from 30% to 25%)
        night_percentage = self._calculate_night_percentage(df)
        if night_percentage >= 0.25:  # Lower threshold!
            confidence = min(0.95, night_percentage * 1.8)  # Increased multiplier
            desc = f"Night owl - {night_percentage:.0%} of energy used at night (10 PM - 6 AM)"
            # Soft-match hint for borderline/confidence cases
            if confidence < 0.6:
                desc = "Possible " + desc
            patterns.append(self._create_pattern(
                PatternType.NIGHT_OWL,
                confidence,
                desc,
                [f"Night usage: {night_percentage:.1%}"],
                df, user_id, start_date, end_date,
                {"night_percentage": night_percentage}
            ))
        
        # 2. EVENING PEAKER (NEW: High usage 6-10 PM)
        evening_percentage = self._calculate_evening_percentage(df)
        if evening_percentage >= 0.25:
            patterns.append(self._create_pattern(
                PatternType.EVENING_PEAKER,
                min(0.9, evening_percentage * 1.8),
                f"Evening peaker - {evening_percentage:.0%} of energy used in evening (6-10 PM)",
                [f"Evening usage: {evening_percentage:.1%}"],
                df, user_id, start_date, end_date,
                {"evening_percentage": evening_percentage}
            ))
        
        # 3. MORNING BIRD (NEW: High usage 6-9 AM)
        morning_percentage = self._calculate_morning_percentage(df)
        if morning_percentage >= 0.20:  # 20% threshold
            patterns.append(self._create_pattern(
                PatternType.MORNING_BIRD,
                min(0.85, morning_percentage * 2.0),
                f"Morning bird - {morning_percentage:.0%} of energy used in morning (6-9 AM)",
                [f"Morning usage: {morning_percentage:.1%}"],
                df, user_id, start_date, end_date,
                {"morning_percentage": morning_percentage}
            ))
        
        # 4. DAYTIME WORKER (High usage 9 AM - 5 PM)
        daytime_percentage = self._calculate_daytime_percentage(df)
        if daytime_percentage >= 0.35:
            patterns.append(self._create_pattern(
                PatternType.DAYTIME_WORKER,
                min(0.9, daytime_percentage * 1.5),
                f"Daytime worker - {daytime_percentage:.0%} of energy used during work hours",
                [f"Daytime usage: {daytime_percentage:.1%}"],
                df, user_id, start_date, end_date,
                {"daytime_percentage": daytime_percentage}
            ))
        
        # 5. WEEKDAY WARRIOR (lowered threshold from 1.3x to 1.2x)
        if len(df['date'].unique()) >= 7:
            weekday_ratio = self._calculate_weekday_ratio(df)
            if weekday_ratio >= 1.2:  # Lower threshold!
                patterns.append(self._create_pattern(
                    PatternType.WEEKDAY_WARRIOR,
                    min(0.9, (weekday_ratio - 1) * 3),  # More sensitive
                    f"Weekday warrior - {weekday_ratio:.1f}x more energy on weekdays",
                    [f"Weekday/weekend ratio: {weekday_ratio:.2f}x"],
                    df, user_id, start_date, end_date,
                    {"weekday_ratio": weekday_ratio}
                ))
        
        # 6. WEEKEND SPIKER (NEW: Higher on weekends)
        if len(df['date'].unique()) >= 7:
            weekend_ratio = self._calculate_weekend_ratio(df)
            if weekend_ratio >= 1.2:
                patterns.append(self._create_pattern(
                    PatternType.WEEKEND_SPIKER,
                    min(0.9, (weekend_ratio - 1) * 3),
                    f"Weekend spiker - {weekend_ratio:.1f}x more energy on weekends",
                    [f"Weekend/weekday ratio: {weekend_ratio:.2f}x"],
                    df, user_id, start_date, end_date,
                    {"weekend_ratio": weekend_ratio}
                ))
        
        # 7. CONSISTENT USER (lowered threshold)
        consistency_score = self._calculate_consistency(df)
        if consistency_score >= 0.7:  # 0-1 scale, higher = more consistent
            patterns.append(self._create_pattern(
                PatternType.CONSISTENT_USER,
                consistency_score,
                "Consistent user - stable daily energy usage",
                [f"Consistency score: {consistency_score:.1%}"],
                df, user_id, start_date, end_date,
                {"consistency_score": consistency_score}
            ))
        
        # 8. LOW/HIGH CONSUMER (NEW: Compared to average)
        avg_daily = df.groupby('date')['kwh'].sum().mean()
        if avg_daily > 0:
            # Compare to typical household (20-30 kWh/day)
            typical_daily = 25.0  # kWh
            
            if avg_daily < typical_daily * 0.7:  # 30% below typical
                patterns.append(self._create_pattern(
                    PatternType.LOW_CONSUMER,
                    min(0.9, (typical_daily - avg_daily) / typical_daily),
                    f"Low consumer - uses {avg_daily:.1f} kWh/day ({avg_daily/typical_daily:.0%} of typical)",
                    [f"Daily average: {avg_daily:.1f} kWh", f"Typical: {typical_daily:.1f} kWh"],
                    df, user_id, start_date, end_date,
                    {"avg_daily": avg_daily, "typical_daily": typical_daily}
                ))
            elif avg_daily > typical_daily * 1.3:  # 30% above typical
                patterns.append(self._create_pattern(
                    PatternType.HIGH_CONSUMER,
                    min(0.9, (avg_daily - typical_daily) / typical_daily),
                    f"High consumer - uses {avg_daily:.1f} kWh/day ({avg_daily/typical_daily:.0%} of typical)",
                    [f"Daily average: {avg_daily:.1f} kWh", f"Typical: {typical_daily:.1f} kWh"],
                    df, user_id, start_date, end_date,
                    {"avg_daily": avg_daily, "typical_daily": typical_daily}
                ))
        
        return patterns
    
    # HELPER METHODS FOR NEW PATTERNS
    
    def _calculate_evening_percentage(self, df: pd.DataFrame) -> float:
        """Evening hours: 6 PM - 10 PM (18-22)"""
        evening_mask = (df['hour'] >= 18) & (df['hour'] < 22)
        evening_kwh = df[evening_mask]['kwh'].sum()
        total_kwh = df['kwh'].sum()
        return evening_kwh / total_kwh if total_kwh > 0 else 0
    
    def _calculate_morning_percentage(self, df: pd.DataFrame) -> float:
        """Morning hours: 6 AM - 9 AM (6-9)"""
        morning_mask = (df['hour'] >= 6) & (df['hour'] < 9)
        morning_kwh = df[morning_mask]['kwh'].sum()
        total_kwh = df['kwh'].sum()
        return morning_kwh / total_kwh if total_kwh > 0 else 0
    
    def _calculate_daytime_percentage(self, df: pd.DataFrame) -> float:
        """Daytime hours: 9 AM - 5 PM (9-17)"""
        daytime_mask = (df['hour'] >= 9) & (df['hour'] < 17)
        daytime_kwh = df[daytime_mask]['kwh'].sum()
        total_kwh = df['kwh'].sum()
        return daytime_kwh / total_kwh if total_kwh > 0 else 0
    
    def _calculate_weekend_ratio(self, df: pd.DataFrame) -> float:
        """Weekend to weekday ratio"""
        weekend_avg = df[df['is_weekend']]['kwh'].mean()
        weekday_avg = df[~df['is_weekend']]['kwh'].mean()
        return weekend_avg / weekday_avg if weekday_avg > 0 else 1
    
    def _calculate_consistency(self, df: pd.DataFrame) -> float:
        """Calculate consistency score (0-1)"""
        daily_totals = df.groupby('date')['kwh'].sum()
        if len(daily_totals) < 3:
            return 0
        
        # Coefficient of variation (inverted: lower CV = higher consistency)
        cv = daily_totals.std() / daily_totals.mean() if daily_totals.mean() > 0 else 1
        # Convert to 0-1 score (lower CV = higher score)
        return max(0, 1 - cv)
    
    # EXISTING METHODS (update thresholds)
    def _calculate_night_percentage(self, df: pd.DataFrame) -> float:
        """Night hours: 10 PM - 6 AM (22-6)"""
        night_mask = (df['hour'] >= 22) | (df['hour'] < 6)
        night_kwh = df[night_mask]['kwh'].sum()
        total_kwh = df['kwh'].sum()
        return night_kwh / total_kwh if total_kwh > 0 else 0
    
    def _calculate_weekday_ratio(self, df: pd.DataFrame) -> float:
        """Weekday to weekend ratio"""
        weekday_avg = df[~df['is_weekend']]['kwh'].mean()
        weekend_avg = df[df['is_weekend']]['kwh'].mean()
        return weekday_avg / weekend_avg if weekend_avg > 0 else 1
    
    def _prepare_dataframe(self, data: List[Tuple[datetime, float]]) -> pd.DataFrame:
        """Prepare DataFrame for analysis"""
        df = pd.DataFrame(data, columns=['datetime', 'kwh'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # Extract features
        df['date'] = df['datetime'].dt.date
        df['hour'] = df['datetime'].dt.hour
        df['day_of_week'] = df['datetime'].dt.dayofweek  # 0=Monday
        df['is_weekend'] = df['day_of_week'] >= 5
        
        return df
    
    def _create_pattern(self, pattern_type: PatternType, confidence: float,
                       description: str, evidence: List[str], 
                       df: pd.DataFrame, user_id: int, 
                       start_date: date, end_date: date,
                       metadata: dict = None) -> EnergyPattern:
        """Helper to create pattern objects"""
        return EnergyPattern(
            id=None,
            user_id=user_id,
            pattern_type=pattern_type,
            confidence=round(float(confidence), 2), 
            description=description,
            detected_at=datetime.now(),
            start_date=start_date,
            end_date=end_date
        )
    
    