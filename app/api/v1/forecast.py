# app/api/v1/forecast.py
# Forecast endpoints for the Smart Energy Dashboard.
# - Prefix is "/forecast" (the API version "/api/v1" is added in app.main)
# - Loads PV/consumption/price CSVs and produces a simple baseline forecast
# - Keeps response shapes stable so the UI can consume them easily
# Design notes:
#   SRP: this router handles HTTP and delegates forecasting logic
#   DIP: callers depend on stable JSON contracts, not model internals

from __future__ import annotations

from datetime import datetime
from typing import List, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# For now we keep forecasting logic very small and local to the router.
# Later we can move it into modules/forecast/ as the project grows.
import pandas as pd
from pathlib import Path

router = APIRouter(prefix="/forecast", tags=["forecast"])

PV_DIR = Path("infra") / "data" / "pv"


# ---------- DTOs ----------------------------------------------------------------

Target = Literal["pv"]

class TrainRequest(BaseModel):
    target: Target = Field(default="pv")
    years: List[int] = Field(default_factory=lambda: [2025, 2026])
    key_template: str = Field(default="pv_{year}_hourly")  # file stem without .csv


class TrainResponse(BaseModel):
    target: Target
    years: List[int]
    rows_used: int
    note: str


class ForecastPoint(BaseModel):
    timestamp: datetime
    value: float


class ForecastResponse(BaseModel):
    target: Target
    hours: int
    rows: List[ForecastPoint]


# ---------- helpers -------------------------------------------------------------

def _pv_csv_path(year: int, key_template: str) -> Path:
    key = key_template.format(year=year).strip()
    p = PV_DIR / f"{key}.csv"
    if not p.exists():
        raise FileNotFoundError(f"PV series not found: {p}")
    return p


def _load_pv(year: int, key_template: str) -> pd.DataFrame:
    p = _pv_csv_path(year, key_template)
    df = pd.read_csv(p)

    # Expect canonical columns from your PV data:
    # datetime, production_kw
    if "datetime" not in df.columns or "production_kw" not in df.columns:
        raise ValueError(f"PV CSV '{p.name}' must contain columns: datetime, production_kw")

    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    df = df.sort_values("datetime").reset_index(drop=True)

    # Convert hourly kW → kWh for a 1-hour bucket (kW * 1h)
    df["pv_kwh"] = df["production_kw"].astype(float).clip(lower=0) * 1.0
    return df[["datetime", "pv_kwh"]]


def _baseline_next_hours(df: pd.DataFrame, hours: int) -> pd.DataFrame:
    """
    Very simple baseline forecast:
    predict next 'hours' by repeating the last 24h profile (seasonality-free baseline).
    This is intentionally basic for a first version.
    """
    if df.empty:
        raise ValueError("no data available for forecasting")

    last_ts = df["datetime"].iloc[-1]
    history = df.tail(24)
    if len(history) < 24:
        raise ValueError("need at least 24 rows for baseline forecast")

    values = list(history["pv_kwh"].values)
    out_rows = []
    for h in range(hours):
        ts = last_ts + pd.Timedelta(hours=h + 1)
        out_rows.append((ts, float(values[h % 24])))

    out = pd.DataFrame(out_rows, columns=["datetime", "pv_kwh_pred"])
    return out


# ---------- endpoints -----------------------------------------------------------


@router.get("", response_model=dict)
def forecast_root() -> dict:
    """
    Forecast service root.
    Provides a lightweight health/shape check for the forecast module.
    """
    return {
        "service": "forecast",
        "status": "ok",
        "endpoints": [
            "/api/v1/forecast/next",
            "/api/v1/forecast/train",
        ],
    }


@router.post("/train", response_model=TrainResponse)
def train(req: TrainRequest) -> TrainResponse:
    """
    Placeholder training endpoint.
    For now: validates data availability and reports how much data would be used.
    Later: can persist an actual model.
    """
    try:
        frames = [_load_pv(y, req.key_template) for y in req.years]
        df = pd.concat(frames, ignore_index=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return TrainResponse(
        target=req.target,
        years=req.years,
        rows_used=int(len(df)),
        note="baseline forecast v1 uses a repeated last-24h profile; no model persisted yet",
    )


@router.get("/next", response_model=ForecastResponse)
def forecast_next(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to forecast"),
    year: int = Query(2027, description="Which dataset year to use as the current history"),
    key_template: str = Query("pv_{year}_hourly", description="PV series key template"),
) -> ForecastResponse:
    """
    Return a next-horizon forecast as [{"timestamp": ..., "value": ...}, ...].
    """
    try:
        df = _load_pv(year, key_template)
        out = _baseline_next_hours(df, hours=hours)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    rows = [
        ForecastPoint(timestamp=row["datetime"].to_pydatetime(), value=float(row["pv_kwh_pred"]))
        for _, row in out.iterrows()
    ]
    return ForecastResponse(target="pv", hours=hours, rows=rows)
