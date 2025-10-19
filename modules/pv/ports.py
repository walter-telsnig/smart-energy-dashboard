from typing import Protocol
from .domain import PVTimeSeries

class PVRepositoryPort(Protocol):
    def load_series(self, name: str) -> PVTimeSeries:
        """Load a PV timeseries by file name or logical key (e.g., 'pv_2026_hourly')."""
        ...
