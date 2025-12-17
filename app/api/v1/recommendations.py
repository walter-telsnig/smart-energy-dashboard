# Recommendation endpoints for the Smart Energy Dashboard.
# - Prefix is "/recommendations" (API version added in app.main)
# - Delegates decision logic to modules.recommendations.use_cases
#
# Design notes:
#   SRP: HTTP + orchestration only
#   DIP: depends on stable use-case interface

from __future__ import annotations

from datetime import datetime
from typing import List, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from modules.recommendations.use_cases import generate_recommendations

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


# ---------- endpoints -----------------------------------------------------------

@router.get("", response_model=RecommendationsResponse)
def recommendations(
    hours: int = Query(24, ge=1, le=168),
    price_threshold_eur_kwh: float = Query(0.12, ge=0.0, le=5.0),
) -> RecommendationsResponse:
    """
    Return recommendations starting from today.
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
