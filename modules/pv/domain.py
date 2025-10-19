from dataclasses import dataclass
from typing import List, Tuple

# SRP: Domain type for PV series returned by the app layer
@dataclass(frozen=True)
class PVPoint:
    timestamp: str     # ISO8601 (UTC)
    production_kw: float

@dataclass(frozen=True)
class PVTimeSeries:
    points: List[PVPoint]
