from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Literal, Optional, Any, Dict

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from modules.battery.domain import BatteryParams
from modules.recommendations.cost_model import compare_costs, CostParams
from modules.recommendations.use_cases import build_planning_inputs, generate_recommendations

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

Action = Literal["charge", "discharge", "shift_load", "idle"]


# ---------------- DTOs ----------------

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


# ---------------- helpers ----------------

def _default_home_battery() -> BatteryParams:
    """
    Simple, reasonable "home battery" defaults for v1.
    We intentionally do NOT expose SoC/tariff/export complexity in the API.
    """
    return BatteryParams(
        capacity_kwh=10.0,
        soc_min=0.10,
        soc_max=0.95,
        eta_c=0.92,
        eta_d=0.92,
        p_charge_max_kw=5.0,
        p_discharge_max_kw=5.0,
        initial_soc_kwh=5.0,
    )


def _parse_iso_z(ts: str) -> datetime:
    """
    Parse ISO timestamps like '2025-12-18T00:00:00Z' into aware datetime (UTC).
    Keeps mypy happy and avoids relying on implicit pydantic parsing in code paths.
    """
    s = ts.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s).astimezone(timezone.utc)


def _rows_to_response_points(rows: List[Dict[str, Any]]) -> List[RecommendationPoint]:
    out: List[RecommendationPoint] = []
    for r in rows:
        ts_raw = r.get("timestamp")
        if isinstance(ts_raw, datetime):
            ts = ts_raw
        elif isinstance(ts_raw, str):
            ts = _parse_iso_z(ts_raw)
        else:
            raise ValueError(f"Invalid timestamp value: {ts_raw!r}")

        out.append(
            RecommendationPoint(
                timestamp=ts,
                action=r["action"],
                reason=str(r.get("reason", "")),
                score=float(r.get("score", 0.0)),
            )
        )
    return out


# ---------------- endpoints ----------------

@router.get("", response_model=RecommendationsResponse)
def recommendations(
    hours: int = Query(24, ge=1, le=168),

    # Keep this optional for now but hide it from Swagger/UI to reduce confusion.
    # If omitted => your use_cases can auto-compute it (e.g., percentile in window).
    price_threshold_eur_kwh: Optional[float] = Query(
        None, ge=0.0, le=5.0, include_in_schema=False
    ),

    battery_enabled: bool = Query(True),
) -> RecommendationsResponse:
    """
    Human-friendly recommendations for the next N hours.

    v1 simplification:
    - Battery parameters are fixed to common home defaults (not user-configured yet).
    - Weather is used internally by the recommendation logic (if available in datasets).
    """
    try:
        batt = _default_home_battery()

        rows = generate_recommendations(
            hours=hours,
            price_threshold_eur_kwh=price_threshold_eur_kwh,
            battery_enabled=battery_enabled,
            battery_params=batt,
        )

        points = _rows_to_response_points(rows)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return RecommendationsResponse(hours=hours, rows=points)


@router.get("/cost-summary", response_model=CostSummaryResponse)
def cost_summary(
    hours: int = Query(24, ge=1, le=168),

    # keep consistent signature internally, but hide from UI
    price_threshold_eur_kwh: Optional[float] = Query(
        None, ge=0.0, le=5.0, include_in_schema=False
    ),

    battery_enabled: bool = Query(True),
) -> CostSummaryResponse:
    """
    Simple cost summary for the SAME planning window.

    v1 simplification:
    - We compute IMPORT COST only (what the user pays to buy energy).
    - Export revenue is forced to 0 to avoid confusing "negative costs".
    """
    try:
        plan = build_planning_inputs(hours)

        batt = _default_home_battery()

        # Force "no export revenue" for v1 simplicity:
        # - feed_in tariff = 0.0 means exporting PV does not reduce your cost
        # - prevents negative baseline costs in PV-heavy synthetic datasets
        cost_params = CostParams(export_mode="feed_in", feed_in_tariff_eur_per_kwh=0.0)

        result = compare_costs(
            plan,
            battery_enabled=battery_enabled,
            battery_params=batt,
            cost_params=cost_params,
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
