from typing import Protocol, List
from .domain import PVTimeSeries

class PVRepositoryPort(Protocol):
    def load_series(self, name: str) -> PVTimeSeries:
        """Load a PV timeseries by file name or logical key (e.g., 'pv_2026_hourly')."""
        ...
    def list_series(self) -> List[str]: ...