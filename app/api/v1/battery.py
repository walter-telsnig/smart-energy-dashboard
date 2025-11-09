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
import os
import pandas as pd

from modules.battery.domain import BatteryParams
from modules.battery.schemas import (
    BatteryParamsIn,
    BatterySimRequest,
    BatterySimResponse,
    BatteryPoint,
    BatteryCostRequest,
    BatteryCostResponse,
    BatteryCostPoint,
)
from modules.battery.service import simulate, _load_series, load_price, compute_costs

router = APIRouter(prefix="/api/v1/battery", tags=["battery"])

DEFAULT_PV_PATH = os.getenv("PV_CSV_PATH", "infra/data/pv/pv_2025_hourly.csv")
DEFAULT_CONS_PATH = os.getenv("CONS_CSV_PATH", "infra/data/consumption/consumption_2025_hourly.csv")
DEFAULT_PRICE_PATH = os.getenv("PRICE_CSV_PATH", "infra/data/market/price_2025_hourly.csv")

@router.get("/defaults", response_model=BatteryParamsIn)
def get_defaults() -> BatteryParamsIn:
    return BatteryParamsIn(
        capacity_kwh=10.0,
        soc_min=0.05,
        soc_max=0.95,
        eta_c=0.95,
        eta_d=0.95,
        p_charge_max_kw=5.0,
        p_discharge_max_kw=5.0,
    )

@router.post("/simulate", response_model=BatterySimResponse)
def post_simulate(req: BatterySimRequest) -> BatterySimResponse:
    pv_csv = req.pv_csv or DEFAULT_PV_PATH
    cons_csv = req.consumption_csv or DEFAULT_CONS_PATH

    if not os.path.exists(pv_csv):
        raise HTTPException(status_code=400, detail=f"PV csv not found: {pv_csv}")
    if not os.path.exists(cons_csv):
        raise HTTPException(status_code=400, detail=f"Consumption csv not found: {cons_csv}")

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

    # Convert index to a concrete DatetimeIndex to satisfy mypy
    dt_index: pd.DatetimeIndex = pd.to_datetime(res.index)
    points: list[BatteryPoint] = []
    for i, ts_item in enumerate(dt_index):
        ts_iso = ts_item.to_pydatetime().isoformat()
        row = res.iloc[i]
        points.append(
            BatteryPoint(
                datetime=ts_iso,
                soc_kwh=float(row["soc_kwh"]),
                charge_kwh=float(row["charge_kwh"]),
                discharge_kwh=float(row["discharge_kwh"]),
                grid_import_kwh=float(row["grid_import_kwh"]),
                grid_export_kwh=float(row["grid_export_kwh"]),
            )
        )
    return BatterySimResponse(points=points)

@router.post("/cost-summary", response_model=BatteryCostResponse)
def post_cost_summary(req: BatteryCostRequest) -> BatteryCostResponse:
    pv_csv = req.pv_csv or DEFAULT_PV_PATH
    cons_csv = req.consumption_csv or DEFAULT_CONS_PATH
    price_csv = req.price_csv or DEFAULT_PRICE_PATH

    for pth, label in [(pv_csv, "PV"), (cons_csv, "Consumption"), (price_csv, "Price")]:
        if not os.path.exists(pth):
            raise HTTPException(status_code=400, detail=f"{label} csv not found: {pth}")

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
    sim = simulate(p, ts)
    price = load_price(price_csv, req.start, req.end)
    df = compute_costs(
        sim,
        price,
        export_mode=req.export_mode,
        feed_in_tariff_eur_per_kwh=req.feed_in_tariff_eur_per_kwh,
    )

    total_import = float(df["import_cost_eur"].sum())
    total_export = float(df["export_revenue_eur"].sum())
    total_net = float(df["net_cost_eur"].sum())

    # Daily breakdown using a concrete DatetimeIndex
    daily = df.resample("D").sum(numeric_only=True)
    daily_index: pd.DatetimeIndex = pd.DatetimeIndex(daily.index)
    points: list[BatteryCostPoint] = []
    for i, ts_item in enumerate(daily_index):
        row = daily.iloc[i]
        points.append(
            BatteryCostPoint(
                datetime=ts_item.to_pydatetime().isoformat(),
                import_cost_eur=float(row.get("import_cost_eur", 0.0)),
                export_revenue_eur=float(row.get("export_revenue_eur", 0.0)),
                net_cost_eur=float(row.get("net_cost_eur", 0.0)),
            )
        )

    return BatteryCostResponse(
        total_import_cost_eur=total_import,
        total_export_revenue_eur=total_export,
        total_net_cost_eur=total_net,
        daily_breakdown=points,
    )
