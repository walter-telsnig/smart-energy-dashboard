
from datetime import datetime, timedelta, date
from modules.pattern.services.pattern_analyzer import PatternAnalyzer
from modules.pattern.domain import PatternType


def make_near_night_data(days: int = 31, night_val: float = 0.83688, day_val: float = 1.0):
    """Create hourly timeseries where night percentage ~ 0.295 (near threshold)."""
    data = []
    base = datetime(2026, 1, 1)
    for d in range(days):
        for h in range(24):
            ts = base + timedelta(days=d, hours=h)
            if h >= 22 or h < 6:
                v = night_val
            else:
                v = day_val
            data.append((ts, v))
    return data


def test_night_soft_match():
    data = make_near_night_data()
    analyzer = PatternAnalyzer()

    start_date = date(2026, 1, 1)
    end_date = date(2026, 1, 31)

    patterns = analyzer.analyze_consumption(data, user_id=1, start_date=start_date, end_date=end_date)

    # Expect a soft night_owl pattern (one pattern) with confidence below 0.6
    assert len(patterns) >= 1
    night_patterns = [p for p in patterns if p.pattern_type == PatternType.NIGHT_OWL]
    assert len(night_patterns) == 1
    p = night_patterns[0]
    assert p.confidence < 0.6
    assert "Possible" in p.description
