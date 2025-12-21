# ==============================================
# File: app/api/v1/battery.py
# ==============================================
"""
FastAPI router for battery simulation endpoints.

Endpoints:
- POST /api/v1/battery/simulate : run greedy simulation over a time window.
- POST /api/v1/battery/cost-summary : run simulation + compute costs
- GET  /api/v1/battery/defaults : return recommended default parameters.

Notes:
- Router orchestrates I/O only, delegates logic to service/domain (DIP).
- CSV paths default to repo layout but can be overridden in the request.
"""

from __future__ import annotations

import os

import pandas as pd
from fastapi import APIRouter, HTTPException

from modules.battery.domain import BatteryParams
from modules.battery.schemas import (
    BatteryCostPoint,
    BatteryCostRequest,
    BatteryCostResponse,
    BatteryParamsIn,
    BatteryPoint,
    BatterySimRequest,
    BatterySimResponse,
)
from modules.battery.service import compute_costs, load_price, load_series, simulate

# IMPORTANT:
# In app/main.py you include routers with prefix="/api/v1"
# so routers here MUST NOT include "/api/v1" again.
router = APIRouter(prefix="/battery", tags=["battery"])

DEFAULT_PV_PATH = os.getenv("PV_CSV_PATH", "infra/data/pv/pv_2025_hourly.csv")
DEFAULT_CONS_PATH = os.getenv("CONS_CSV_PATH", "infra/data/consumption/consumption_2025_hourly.csv")
DEFAULT_PRICE_PATH = os.getenv("PRICE_CSV_PATH", "infra/data/market/price_2025_hourly.csv")


@router.get("/defaults", response_model=BatteryParamsIn)
def get_defaults() -> BatteryParamsIn:
    # Simple, common home-battery-like defaults
    return BatteryParamsIn(
        capacity_kwh=10.0,
        soc_min=0.10,
        soc_max=0.95,
        eta_c=0.92,
        eta_d=0.92,
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

    params = BatteryParams(
        capacity_kwh=req.params.capacity_kwh,
        soc_min=req.params.soc_min,
        soc_max=req.params.soc_max,
        eta_c=req.params.eta_c,
        eta_d=req.params.eta_d,
        p_charge_max_kw=req.params.p_charge_max_kw,
        p_discharge_max_kw=req.params.p_discharge_max_kw,
        # BatterySimRequest schema currently has no initial_soc_kwh -> domain defaults to 50% capacity
        initial_soc_kwh=None,
    )

    ts = load_series(pv_csv, cons_csv, req.start, req.end)
    sim_df = simulate(params, ts)

    # Ensure a concrete DatetimeIndex (UTC)
    dt_index: pd.DatetimeIndex = pd.to_datetime(sim_df.index, utc=True)

    points: list[BatteryPoint] = []
    for i, ts_item in enumerate(dt_index):
        row = sim_df.iloc[i]
        points.append(
            BatteryPoint(
                datetime=ts_item.strftime("%Y-%m-%dT%H:%M:%SZ"),
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

    params = BatteryParams(
        capacity_kwh=req.params.capacity_kwh,
        soc_min=req.params.soc_min,
        soc_max=req.params.soc_max,
        eta_c=req.params.eta_c,
        eta_d=req.params.eta_d,
        p_charge_max_kw=req.params.p_charge_max_kw,
        p_discharge_max_kw=req.params.p_discharge_max_kw,
        initial_soc_kwh=None,
    )

    ts = load_series(pv_csv, cons_csv, req.start, req.end)
    sim_df = simulate(params, ts)

    price_eur_mwh = load_price(price_csv, req.start, req.end)

    df = compute_costs(
        sim_df,
        price_eur_mwh,
        export_mode=req.export_mode,
        feed_in_tariff_eur_per_kwh=req.feed_in_tariff_eur_per_kwh,
    )

    total_import = float(df["import_cost_eur"].sum())
    total_export = float(df["export_revenue_eur"].sum())
    total_net = float(df["net_cost_eur"].sum())

    # Daily breakdown
    daily = df.resample("D").sum(numeric_only=True)
    daily_index: pd.DatetimeIndex = pd.to_datetime(daily.index, utc=True)

    points: list[BatteryCostPoint] = []
    for i, ts_item in enumerate(daily_index):
        row = daily.iloc[i]
        points.append(
            BatteryCostPoint(
                datetime=ts_item.strftime("%Y-%m-%dT%H:%M:%SZ"),
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
