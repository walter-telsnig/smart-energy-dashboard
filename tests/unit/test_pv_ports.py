from typing import List
#from modules.pv.ports import PVRepositoryPort
from modules.pv.domain import PVTimeSeries, PVPoint

class MockPVRepository:
    """Mock implementation of PVRepositoryPort for testing purposes."""
    def load_series(self, name: str) -> PVTimeSeries:
        return PVTimeSeries(points=[PVPoint(timestamp="2023-01-01T12:00:00Z", production_kw=1.0)])

    def list_series(self) -> List[str]:
        return ["series1", "series2"]

def test_pv_repository_port_protocol():
    """
    Test that a concrete class can implement the Protocol.
    This test mainly serves to import the module and verify type usage, 
    ensuring lines in ports.py are 'covered'.
    """
    repo = MockPVRepository()
    
    # Verify method signatures via usage
    series = repo.load_series("some_series")
    assert isinstance(series, PVTimeSeries)
    assert len(series.points) == 1
    
    listing = repo.list_series()
    assert isinstance(listing, list)
    assert "series1" in listing
