from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from modules.battery.domain import BatteryParams
from modules.recommendations.cost_model import compare_costs, CostParams
from modules.recommendations.use_cases import build_planning_inputs, generate_recommendations

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

Action = Literal["charge", "discharge", "shift_load", "idle"]


class RecommendationPoint(BaseModel):
    timestamp: datetime
    action: Action
    reason: str
    score: float = Field(ge=0.0, le=1.0)


class RecommendationsResponse(BaseModel):
    hours: int
    rows: List[RecommendationPoint]


class CostSummaryResponse(BaseModel):
    hours: int
    baseline_cost_eur: float
    optimized_cost_eur: float
    savings_eur: float
    savings_percent: float


@router.get("", response_model=RecommendationsResponse)
def recommendations(
    hours: int = Query(24, ge=1, le=168),

    # If omitted => AUTO (75th percentile in window)
    price_threshold_eur_kwh: Optional[float] = Query(None, ge=0.0, le=5.0),

    # battery controls
    battery_enabled: bool = Query(True),

    capacity_kwh: float = Query(10.0, ge=0.0),
    soc_min: float = Query(0.10, ge=0.0, le=1.0),
    soc_max: float = Query(0.95, ge=0.0, le=1.0),
    eta_c: float = Query(0.92, ge=0.0, le=1.0),
    eta_d: float = Query(0.92, ge=0.0, le=1.0),
    p_charge_max_kw: float = Query(5.0, ge=0.0),
    p_discharge_max_kw: float = Query(5.0, ge=0.0),
    initial_soc_kwh: float = Query(5.0, ge=0.0),
) -> RecommendationsResponse:
    try:
        batt = BatteryParams(
            capacity_kwh=capacity_kwh,
            soc_min=soc_min,
            soc_max=soc_max,
            eta_c=eta_c,
            eta_d=eta_d,
            p_charge_max_kw=p_charge_max_kw,
            p_discharge_max_kw=p_discharge_max_kw,
            initial_soc_kwh=initial_soc_kwh,
        )

        rows = generate_recommendations(
            hours=hours,
            price_threshold_eur_kwh=price_threshold_eur_kwh,
            battery_enabled=battery_enabled,
            battery_params=batt,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return RecommendationsResponse(hours=hours, rows=[RecommendationPoint(**r) for r in rows])


@router.get("/cost-summary", response_model=CostSummaryResponse)
def cost_summary(
    hours: int = Query(24, ge=1, le=168),

    # keep consistent signature with /recommendations (even if cost does not use it directly)
    price_threshold_eur_kwh: Optional[float] = Query(None, ge=0.0, le=5.0),

    battery_enabled: bool = Query(True),

    capacity_kwh: float = Query(10.0, ge=0.0),
    soc_min: float = Query(0.10, ge=0.0, le=1.0),
    soc_max: float = Query(0.95, ge=0.0, le=1.0),
    eta_c: float = Query(0.92, ge=0.0, le=1.0),
    eta_d: float = Query(0.92, ge=0.0, le=1.0),
    p_charge_max_kw: float = Query(5.0, ge=0.0),
    p_discharge_max_kw: float = Query(5.0, ge=0.0),
    initial_soc_kwh: float = Query(5.0, ge=0.0),

    export_mode: Literal["market", "feed_in"] = Query("feed_in"),
    feed_in_tariff_eur_per_kwh: float = Query(0.08, ge=0.0),
) -> CostSummaryResponse:
    try:
        plan = build_planning_inputs(hours)

        batt = BatteryParams(
            capacity_kwh=capacity_kwh,
            soc_min=soc_min,
            soc_max=soc_max,
            eta_c=eta_c,
            eta_d=eta_d,
            p_charge_max_kw=p_charge_max_kw,
            p_discharge_max_kw=p_discharge_max_kw,
            initial_soc_kwh=initial_soc_kwh,
        )

        result = compare_costs(
            plan,
            battery_enabled=battery_enabled,
            battery_params=batt,
            cost_params=CostParams(export_mode=export_mode, feed_in_tariff_eur_per_kwh=feed_in_tariff_eur_per_kwh),
        )

        baseline = float(result["baseline_cost_eur"])
        optimized = float(result["recommended_cost_eur"])
        savings = float(result["savings_eur"])
        savings_pct = (savings / baseline) * 100 if baseline > 0 else 0.0

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return CostSummaryResponse(
        hours=hours,
        baseline_cost_eur=round(baseline, 2),
        optimized_cost_eur=round(optimized, 2),
        savings_eur=round(savings, 2),
        savings_percent=round(savings_pct, 2),
    )
