# ==============================================
# File: modules/battery/domain.py
# ==============================================
"""
Domain objects for the Battery module.

Design Principles applied:
- SRP: Keep battery parameters and pure domain logic in a small, cohesive file.
- DIP: API/service layers depend on these abstractions, not on concrete I/O.
- CCP: All change related to battery math/constraints is localized here.

TODOs:
- [ ] Consider temperature/aging effects in efficiency in later milestones.
- [ ] Add validation for corner-cases (e.g., zero capacity) if needed.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class BatteryParams:
    """Immutable battery configuration.

    Attributes:
        capacity_kwh: Usable capacity of the battery (kWh).
        soc_min: Minimum allowable state of charge (fraction 0..1).
        soc_max: Maximum allowable state of charge (fraction 0..1).
        eta_c: Charge efficiency (0..1).
        eta_d: Discharge efficiency (0..1).
        p_charge_max_kw: Max charge power (kW). For hourly steps, kW ~= kWh/step.
        p_discharge_max_kw: Max discharge power (kW).
    """
    capacity_kwh: float = 10.0
    soc_min: float = 0.05
    soc_max: float = 0.95
    eta_c: float = 0.95
    eta_d: float = 0.95
    p_charge_max_kw: float = 5.0
    p_discharge_max_kw: float = 5.0

    def clamp_soc(self, soc: float) -> float:
        return max(self.soc_min, min(self.soc_max, soc))