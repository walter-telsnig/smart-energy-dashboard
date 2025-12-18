"""
Domain objects for the Battery module.

Important fix:
- soc_min / soc_max are FRACTIONS (0..1)
- clamp_soc must clamp SOC in kWh to [capacity*soc_min, capacity*soc_max]
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class BatteryParams:
    """Immutable battery configuration.

    Attributes:
        capacity_kwh: Usable capacity of the battery (kWh).
        soc_min: Minimum allowable SoC (fraction 0..1).
        soc_max: Maximum allowable SoC (fraction 0..1).
        eta_c: Charge efficiency (0..1).
        eta_d: Discharge efficiency (0..1).
        p_charge_max_kw: Max charge power (kW). For hourly steps, kW ~= kWh/step.
        p_discharge_max_kw: Max discharge power (kW).
        initial_soc_kwh: Initial SoC in kWh. If None, defaults to 50% of capacity.
    """
    capacity_kwh: float = 10.0
    soc_min: float = 0.10
    soc_max: float = 0.95
    eta_c: float = 0.92
    eta_d: float = 0.92
    p_charge_max_kw: float = 5.0
    p_discharge_max_kw: float = 5.0
    initial_soc_kwh: Optional[float] = None

    def soc_min_kwh(self) -> float:
        return float(self.capacity_kwh) * float(self.soc_min)

    def soc_max_kwh(self) -> float:
        return float(self.capacity_kwh) * float(self.soc_max)

    def clamp_soc_kwh(self, soc_kwh: float) -> float:
        return max(self.soc_min_kwh(), min(self.soc_max_kwh(), float(soc_kwh)))

    def initial_soc(self) -> float:
        if self.initial_soc_kwh is None:
            return float(self.capacity_kwh) * 0.50
        return self.clamp_soc_kwh(float(self.initial_soc_kwh))
