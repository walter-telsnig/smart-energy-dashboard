from typing import Protocol, List
from .domain import ConsumptionTimeSeries

class ConsumptionRepositoryPort(Protocol):
    def load_series(self, name: str) -> ConsumptionTimeSeries:
        """Load a consumption timeseries by file name or logical key (e.g., 'consumption_2026_hourly')."""
        ...

    def list_series(self) -> List[str]:
        """List available logical series keys"""
        ...
