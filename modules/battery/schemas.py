# modules/battery/schemas.py
"""
Pydantic request/response contracts for the Battery API.

Design principles:
- OCP: new fields can be added without breaking existing handlers.
- ADP: Keep web schema separate from domain to avoid cyclic deps.
- Mypy-friendly defaults.
"""

from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal

class BatteryParamsIn(BaseModel):
    capacity_kwh: float = Field(10.0, ge=0.0)
    soc_min: float = Field(0.05, ge=0.0, le=1.0)
    soc_max: float = Field(0.95, ge=0.0, le=1.0)
    eta_c: float = Field(0.95, ge=0.0, le=1.0)
    eta_d: float = Field(0.95, ge=0.0, le=1.0)
    p_charge_max_kw: float = Field(5.0, ge=0.0)
    p_discharge_max_kw: float = Field(5.0, ge=0.0)

def _default_params() -> BatteryParamsIn:
    # Explicit named args keep mypy happy
    return BatteryParamsIn(
        capacity_kwh=10.0,
        soc_min=0.05,
        soc_max=0.95,
        eta_c=0.95,
        eta_d=0.95,
        p_charge_max_kw=5.0,
        p_discharge_max_kw=5.0,
    )

class BatterySimRequest(BaseModel):
    """Simulation request for a date range. Assumes hourly resolution."""
    start: str = Field(..., description="Inclusive ISO-8601 start, e.g. 2025-01-01T00:00:00Z")
    end: str = Field(..., description="Exclusive ISO-8601 end, e.g. 2025-01-08T00:00:00Z")
    params: BatteryParamsIn = Field(default_factory=_default_params)
    pv_csv: Optional[str] = Field(None, description="Path to PV csv with columns [datetime, production_*]")
    consumption_csv: Optional[str] = Field(None, description="Path to consumption csv [datetime, consumption_kwh]")

class BatteryPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    datetime: str
    soc_kwh: float
    charge_kwh: float
    discharge_kwh: float
    grid_import_kwh: float
    grid_export_kwh: float

class BatterySimResponse(BaseModel):
    points: List[BatteryPoint]

# ---- Cost summary ----
class BatteryCostRequest(BatterySimRequest):
    price_csv: str = Field(..., description="Path to price csv [datetime, price_eur_mwh]")
    export_mode: Literal["market", "feed_in"] = Field("feed_in")
    feed_in_tariff_eur_per_kwh: float = Field(0.08, ge=0.0)

class BatteryCostPoint(BaseModel):
    datetime: str
    import_cost_eur: float
    export_revenue_eur: float
    net_cost_eur: float

class BatteryCostResponse(BaseModel):
    total_import_cost_eur: float
    total_export_revenue_eur: float
    total_net_cost_eur: float
    daily_breakdown: List[BatteryCostPoint]
