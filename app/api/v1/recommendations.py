# app/api/v1/recommendations.py
# Recommendation endpoints for the Smart Energy Dashboard.
# - Prefix is "/recommendations" (the API version "/api/v1" is added in app.main)
# - Uses forecasted PV and local price/consumption CSVs to suggest actions
# Design notes:
#   SRP: this router focuses on HTTP + high-level orchestration
#   DIP: recommendation logic can later move into a dedicated module

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Literal

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

PV_DIR = Path("infra") / "data" / "pv"
CONS_DIR = Path("infra") / "data" / "consumption"
PRICE_DIR = Path("infra") / "data" / "market"


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


# ---------- helpers -------------------------------------------------------------

def _load_csv(path: Path, required_cols: List[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing file: {path}")
    df = pd.read_csv(path)
    for c in required_cols:
        if c not in df.columns:
            raise ValueError(f"CSV '{path.name}' must contain column '{c}'")
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    return df.sort_values("datetime").reset_index(drop=True)


def _load_inputs(year: int) -> pd.DataFrame:
    pv_path = PV_DIR / f"pv_{year}_hourly.csv"
    cons_path = CONS_DIR / f"consumption_{year}_hourly.csv"
    price_path = PRICE_DIR / f"price_{year}_hourly.csv"

    pv = _load_csv(pv_path, ["datetime", "production_kw"]).rename(columns={"production_kw": "pv_kw"})
    cons = _load_csv(cons_path, ["datetime", "consumption_kwh"]).rename(columns={"consumption_kwh": "load_kwh"})
    price = _load_csv(price_path, ["datetime", "price_eur_mwh"]).rename(columns={"price_eur_mwh": "price_eur_mwh"})

    df = pv.merge(cons, on="datetime").merge(price, on="datetime")
    df["pv_kwh"] = df["pv_kw"].astype(float).clip(lower=0) * 1.0
    df["price_eur_kwh"] = df["price_eur_mwh"] / 1000.0
    return df[["datetime", "pv_kwh", "load_kwh", "price_eur_kwh"]]


def _recommend_rows(df: pd.DataFrame, hours: int, price_threshold: float) -> pd.DataFrame:
    """
    Basic rule-based recommendation for the next 'hours', based on the last 24h pattern.
    This keeps v1 simple and demo-ready.
    """
    if len(df) < 24:
        raise ValueError("need at least 24 hours of history")

    last_ts = df["datetime"].iloc[-1]
    hist = df.tail(24).reset_index(drop=True)

    out = []
    for h in range(hours):
        ts = last_ts + pd.Timedelta(hours=h + 1)
        row = hist.iloc[h % 24]
        surplus = float(row["pv_kwh"]) - float(row["load_kwh"])
        price = float(row["price_eur_kwh"])

        if surplus > 0.2:
            action = "charge"
            reason = f"predicted PV surplus ({surplus:.2f} kWh)"
            score = 0.85
        elif price >= price_threshold and surplus < 0:
            action = "discharge"
            reason = "high price hour; prefer avoiding grid usage"
            score = 0.75
        elif price < price_threshold and surplus > 0:
            action = "shift_load"
            reason = "cheap hour with some PV available; shift flexible loads"
            score = 0.65
        else:
            action = "idle"
            reason = "no clear advantage"
            score = 0.30

        out.append((ts, action, reason, score))

    return pd.DataFrame(out, columns=["datetime", "action", "reason", "score"])


# ---------- endpoints -----------------------------------------------------------

@router.get("", response_model=RecommendationsResponse)
def recommendations(
    hours: int = Query(24, ge=1, le=168, description="Planning horizon in hours"),
    year: int = Query(2027, description="Which dataset year to use as the current history"),
    price_threshold_eur_kwh: float = Query(0.12, ge=0.0, le=5.0, description="Cheap/expensive cut-off in €/kWh"),
) -> RecommendationsResponse:
    """
    Return next-horizon recommendations as [{"timestamp":..., "action":..., "reason":..., "score":...}, ...].
    """
    try:
        df = _load_inputs(year)
        out = _recommend_rows(df, hours=hours, price_threshold=price_threshold_eur_kwh)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    rows = [
        RecommendationPoint(
            timestamp=row["datetime"].to_pydatetime(),
            action=row["action"],
            reason=row["reason"],
            score=float(row["score"]),
        )
        for _, row in out.iterrows()
    ]
    return RecommendationsResponse(hours=hours, rows=rows)
