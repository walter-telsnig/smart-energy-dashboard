from modules.pv.domain import PVPoint, PVTimeSeries

def test_pv_point_creation():
    point = PVPoint(timestamp="2023-01-01T12:00:00Z", production_kw=5.5)
    assert point.timestamp == "2023-01-01T12:00:00Z"
    assert point.production_kw == 5.5

def test_pv_time_series_creation():
    point1 = PVPoint(timestamp="2023-01-01T12:00:00Z", production_kw=5.5)
    point2 = PVPoint(timestamp="2023-01-01T13:00:00Z", production_kw=6.0)
    series = PVTimeSeries(points=[point1, point2])
    
    assert len(series.points) == 2
    assert series.points[0] == point1
    assert series.points[1] == point2
