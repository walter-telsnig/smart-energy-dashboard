# app/api/v1/forecast.py
# Forecast endpoints for the Smart Energy Dashboard.
# - Prefix is "/forecast" (the API version "/api/v1" is added in app.main)
# - Delegates forecasting logic to modules/forecast/use_cases.py
#
# Design notes:
#   SRP: HTTP only
#   DIP: depends on use-cases, not implementation details

from __future__ import annotations

from typing import List, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from modules.forecast.use_cases import forecast_next, train_baseline

router = APIRouter(prefix="/forecast", tags=["forecast"])


# ---------- DTOs ----------------------------------------------------------------

Target = Literal["pv"]


class TrainRequest(BaseModel):
    target: Target = Field(default="pv")
    years: List[int] = Field(default_factory=lambda: [2025, 2026])
    key_template: str = Field(default="pv_{year}_hourly")


class TrainResponse(BaseModel):
    target: Target
    years: List[int]
    rows_used: int
    note: str


class ForecastPoint(BaseModel):
    timestamp: str
    value: float


class ForecastResponse(BaseModel):
    target: Target
    hours: int
    rows: List[ForecastPoint]


# ---------- endpoints -----------------------------------------------------------

@router.get("", response_model=dict)
def forecast_root() -> dict:
    """
    Forecast service root.
    Used for health checks and discoverability.
    """
    return {
        "service": "forecast",
        "status": "ok",
        "endpoints": [
            "/api/v1/forecast/next",
            "/api/v1/forecast/train",
        ],
    }


@router.get("/next", response_model=ForecastResponse)
def forecast_next_endpoint(
    hours: int = Query(24, ge=1, le=168),
    year: int = Query(2027),
    key_template: str = Query("pv_{year}_hourly"),
) -> ForecastResponse:
    try:
        rows = forecast_next(
            year=year,
            hours=hours,
            key_template=key_template,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ForecastResponse(
        target="pv",
        hours=hours,
        rows=[ForecastPoint(**r) for r in rows],
    )

@router.post("/train", response_model=TrainResponse)
def train(req: TrainRequest) -> TrainResponse:
    """
    Placeholder training endpoint.
    """
    try:
        rows_used = train_baseline(req.years, req.key_template)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return TrainResponse(
        target=req.target,
        years=req.years,
        rows_used=rows_used,
        note="baseline forecast v1 repeats last-24h profile; no model persisted yet",
    )
