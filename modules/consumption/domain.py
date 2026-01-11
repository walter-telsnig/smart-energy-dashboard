from dataclasses import dataclass
from typing import List

# SRP: Domain type for Consumption series returned by the app layer
@dataclass(frozen=True)
class ConsumptionPoint:
    timestamp: str     # ISO8601 (UTC)
    consumption_kwh: float

@dataclass(frozen=True)
class ConsumptionTimeSeries:
    points: List[ConsumptionPoint]
