# ==============================================
# File: app/api/v1/battery.py
# ==============================================
"""
FastAPI router for battery simulation endpoints.

Endpoints (Level 2 RMM):
- POST /api/v1/battery/simulate : run greedy simulation over a time window.
- GET  /api/v1/battery/defaults : return recommended default parameters.

Notes:
- The router only orchestrates I/O and delegates to service/domain (DIP).
- Paths to CSVs default to your repo layout but can be overridden in the request.

TODOs:
- [ ] Add auth/permissions when Accounts module introduces roles.
- [ ] Add optional price path to compute costs/benefits inline.
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
#from pydantic import BaseModel
#from typing import List
import os
#import pandas as pd

from modules.battery.domain import BatteryParams
from modules.battery.schemas import (
    BatteryParamsIn,
    BatterySimRequest,
    BatterySimResponse,
    BatteryPoint,
)
from modules.battery.service import simulate, _load_series

router = APIRouter(prefix="/api/v1/battery", tags=["battery"])

# Default locations consistent with your project
DEFAULT_PV_PATH = os.getenv("PV_CSV_PATH", "infra/data/pv/pv_2025_hourly.csv")
DEFAULT_CONS_PATH = os.getenv("CONS_CSV_PATH", "infra/data/consumption/consumption_2025_hourly.csv")


@router.get("/defaults", response_model=BatteryParamsIn)
def get_defaults() -> BatteryParamsIn:
    """Return safe, documented defaults for battery parameters."""
    return BatteryParamsIn()


@router.post("/simulate", response_model=BatterySimResponse)
def post_simulate(req: BatterySimRequest) -> BatterySimResponse:
    # Resolve file paths
    pv_csv = req.pv_csv or DEFAULT_PV_PATH
    cons_csv = req.consumption_csv or DEFAULT_CONS_PATH

    if not os.path.exists(pv_csv):
        raise HTTPException(status_code=400, detail=f"PV csv not found: {pv_csv}")
    if not os.path.exists(cons_csv):
        raise HTTPException(status_code=400, detail=f"Consumption csv not found: {cons_csv}")

    # Compose params and load data
    p = BatteryParams(
        capacity_kwh=req.params.capacity_kwh,
        soc_min=req.params.soc_min,
        soc_max=req.params.soc_max,
        eta_c=req.params.eta_c,
        eta_d=req.params.eta_d,
        p_charge_max_kw=req.params.p_charge_max_kw,
        p_discharge_max_kw=req.params.p_discharge_max_kw,
    )

    ts = _load_series(pv_csv, cons_csv, req.start, req.end)
    res = simulate(p, ts)

    # Build response
    points = [
        BatteryPoint(
            datetime=idx.isoformat(),
            soc_kwh=float(row["soc_kwh"]),
            charge_kwh=float(row["charge_kwh"]),
            discharge_kwh=float(row["discharge_kwh"]),
            grid_import_kwh=float(row["grid_import_kwh"]),
            grid_export_kwh=float(row["grid_export_kwh"]),
        )
        for idx, row in res.iterrows()
    ]
    return BatterySimResponse(points=points)

