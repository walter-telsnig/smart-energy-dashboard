# Recommendation endpoints for the Smart Energy Dashboard.
# - Prefix is "/recommendations" (API version added in app.main)
# - Delegates decision logic to modules.recommendations.use_cases
# - Uses cost_model to compute KPIs
#
# Design notes:
#   SRP: HTTP + orchestration only
#   DIP: depends on stable use-case interfaces

from __future__ import annotations

from datetime import datetime
from typing import List, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from modules.recommendations.use_cases import (
    generate_recommendations,
    load_inputs,
)
from modules.recommendations.cost_model import compare_costs

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


# ---------- DTOs ----------------------------------------------------------------

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


# ---------- endpoints -----------------------------------------------------------

@router.get("", response_model=RecommendationsResponse)
def recommendations(
    hours: int = Query(24, ge=1, le=168),
    price_threshold_eur_kwh: float = Query(0.12, ge=0.0, le=5.0),
) -> RecommendationsResponse:
    """
    Return recommendations starting from the current day.
    """
    try:
        rows = generate_recommendations(
            hours=hours,
            price_threshold_eur_kwh=price_threshold_eur_kwh,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return RecommendationsResponse(
        hours=hours,
        rows=[RecommendationPoint(**r) for r in rows],
    )


@router.get("/cost-summary", response_model=CostSummaryResponse)
def cost_summary(
    hours: int = Query(24, ge=1, le=168),
    price_threshold_eur_kwh: float = Query(0.12, ge=0.0, le=5.0),
) -> CostSummaryResponse:
    """
    Compare electricity cost with vs without recommendations.
    """
    try:
        # Load merged PV / consumption / price data
        df = load_inputs()

        # Limit to planning horizon (most recent hours)
        df = df.tail(hours)

        # Generate recommendations for same horizon
        reco_rows = generate_recommendations(
            hours=hours,
            price_threshold_eur_kwh=price_threshold_eur_kwh,
        )

        reco_df = (
            __import__("pandas")
            .DataFrame(reco_rows)
            .rename(columns={"timestamp": "timestamp"})
        )

        # Compare costs
        result = compare_costs(df, reco_df)

        baseline = result["baseline_cost_eur"]
        optimized = result["recommended_cost_eur"]
        savings = result["savings_eur"]
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