from __future__ import annotations

from typing import List, Literal, TypedDict

import pandas as pd

from modules.timeseries.use_cases import build_today_plan, load_merged_history

Action = Literal["charge", "discharge", "shift_load", "idle"]


class RecommendationRow(TypedDict):
    timestamp: str
    action: Action
    reason: str
    score: float


def _planning_frame(hours: int) -> pd.DataFrame:
    """
    Canonical planning frame:
    - use merged history (pv/load/price + optional weather)
    - build a today-window plan using the shared builder
    """
    history = load_merged_history()
    plan = build_today_plan(hours=hours, history=history)
    return plan


def generate_recommendations(*, hours: int, price_threshold_eur_kwh: float) -> List[RecommendationRow]:
    """
    v1 rule-based recommendations with a light weather integration:
    - Adjust expected PV using cloud cover (reduces PV when cloudy)
    - Use adjusted PV for surplus decisions
    """
    plan = _planning_frame(hours)

    # Weather-aware PV adjustment (simple, transparent heuristic)
    # pv_adj = pv * (1 - alpha * cloud_cover/100), clipped at >=0
    alpha = 0.7
    if "cloud_cover_pct" in plan.columns:
        cc = plan["cloud_cover_pct"].fillna(0).astype(float).clip(0, 100)
        plan["pv_kwh_adj"] = (plan["pv_kwh"].astype(float) * (1 - alpha * (cc / 100.0))).clip(lower=0.0)
    else:
        plan["pv_kwh_adj"] = plan["pv_kwh"].astype(float)

    rows: List[RecommendationRow] = []
    for _, r in plan.iterrows():
        ts = pd.to_datetime(r["datetime"], utc=True)

        pv = float(r["pv_kwh_adj"])
        load = float(r["load_kwh"])
        price = float(r["price_eur_kwh"])
        surplus = pv - load

        cloud = None
        if "cloud_cover_pct" in plan.columns and pd.notna(r.get("cloud_cover_pct")):
            cloud = float(r["cloud_cover_pct"])

        # Decision rules (same spirit as before, but based on adjusted PV)
        if surplus > 0.2:
            action: Action = "charge"
            reason = f"predicted PV surplus ({surplus:.2f} kWh)"
            score = 0.85
        elif price >= price_threshold_eur_kwh and surplus < 0:
            action = "discharge"
            reason = "high price hour; avoid grid usage"
            score = 0.75
        elif price < price_threshold_eur_kwh and pv > 0.2:
            action = "shift_load"
            reason = "cheap hour with PV available"
            score = 0.65
        else:
            action = "idle"
            reason = "no clear advantage"
            score = 0.30

        # Confidence tweak based on cloudiness (optional, but makes weather matter)
        if cloud is not None and cloud > 80 and action in ("charge", "shift_load"):
            score = max(0.0, score - 0.10)
            reason += f" (cloudy: {cloud:.0f}%)"

        rows.append(
            {
                "timestamp": ts.isoformat(),
                "action": action,
                "reason": reason,
                "score": float(min(max(score, 0.0), 1.0)),
            }
        )

    return rows


def build_planning_inputs(hours: int) -> pd.DataFrame:
    """
    Used by cost-summary to ensure KPIs are computed on the SAME horizon
    as the recommendations shown in the UI.
    """
    return _planning_frame(hours)