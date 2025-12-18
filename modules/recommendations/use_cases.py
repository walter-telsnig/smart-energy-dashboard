from __future__ import annotations

from typing import List, Literal, TypedDict, Optional

import numpy as np
import pandas as pd

from modules.battery.domain import BatteryParams
from modules.battery.service import simulate
from modules.timeseries.use_cases import build_today_plan, load_merged_history

Action = Literal["charge", "discharge", "shift_load", "idle"]


class RecommendationRow(TypedDict):
    timestamp: str
    action: Action
    reason: str
    score: float


def build_planning_inputs(hours: int) -> pd.DataFrame:
    history = load_merged_history()
    return build_today_plan(hours=hours, history=history)


def _auto_price_threshold(prices: pd.Series) -> float:
    """
    Auto threshold = 75th percentile of prices in the horizon.
    This avoids confusing the user with a magic number.
    """
    s = pd.to_numeric(prices, errors="coerce").dropna()
    if s.empty:
        return 0.12

    arr = s.astype("float64").to_numpy()
    return float(np.quantile(arr, 0.75))


def generate_recommendations(
    *,
    hours: int,
    price_threshold_eur_kwh: Optional[float],
    battery_enabled: bool,
    battery_params: BatteryParams,
) -> List[RecommendationRow]:
    """
    v2 recommendations:
    - Build a real-data-first planning window (pv/load/price + optional weather)
    - Apply simple weather PV adjustment (cloud cover reduces expected PV)
    - If battery_enabled => simulate SoC and derive actions from actual charge/discharge
    - Provide shift_load suggestions as "advice" during cheap hours (optional)
    """
    plan = build_planning_inputs(hours).copy().reset_index(drop=True)

    # --- Weather-aware PV adjustment (transparent heuristic)
    alpha = 0.70
    if "cloud_cover_pct" in plan.columns:
        cc = plan["cloud_cover_pct"].fillna(0).astype(float).clip(0, 100)
    else:
        cc = pd.Series(0.0, index=plan.index, dtype="float64")

    plan["pv_kwh_adj"] = (plan["pv_kwh"].astype(float) * (1 - alpha * (cc / 100.0))).clip(lower=0.0)

    # --- Threshold (auto if None)
    thr = _auto_price_threshold(plan["price_eur_kwh"]) if price_threshold_eur_kwh is None else float(price_threshold_eur_kwh)

    # --- Battery simulation (if enabled)
    sim_out: Optional[pd.DataFrame] = None
    if battery_enabled:
        ts = plan.copy()
        ts["datetime"] = pd.to_datetime(ts["datetime"], utc=True)
        ts = ts.sort_values("datetime").set_index("datetime")

        sim_in = pd.DataFrame(
            {
                "production_kwh": ts["pv_kwh_adj"].astype(float).clip(lower=0.0),
                "consumption_kwh": ts["load_kwh"].astype(float).clip(lower=0.0),
            },
            index=ts.index,
        )
        sim_out = simulate(battery_params, sim_in)

    rows: List[RecommendationRow] = []

    # Use integer positions to keep mypy happy (iloc/iat want ints)
    for i in range(len(plan)):
        r = plan.iloc[i]

        ts_dt = pd.to_datetime(r["datetime"], utc=True)
        price = float(r["price_eur_kwh"])
        pv = float(r["pv_kwh_adj"])

        cloud: Optional[float] = None
        if "cloud_cover_pct" in plan.columns and pd.notna(r["cloud_cover_pct"]):
            cloud = float(r["cloud_cover_pct"])

        action: Action = "idle"
        reason = "no clear advantage"
        score = 0.30

        if battery_enabled and sim_out is not None:
            ch = float(sim_out["charge_kwh"].iat[i])
            dch = float(sim_out["discharge_kwh"].iat[i])
            soc = float(sim_out["soc_kwh"].iat[i])

            if ch > 0.01:
                action = "charge"
                reason = f"battery charging from PV surplus (SoC {soc:.1f} kWh)"
                score = 0.85
            elif dch > 0.01:
                action = "discharge"
                reason = f"battery discharging to reduce grid import (price {price:.3f} €/kWh)"
                score = 0.80
            else:
                if price <= thr and pv > 0.2:
                    action = "shift_load"
                    reason = f"cheap hour (≤ {thr:.3f} €/kWh) with PV available"
                    score = 0.60
                else:
                    action = "idle"
                    reason = "battery not needed for this hour"
                    score = 0.35
        else:
            if price <= thr and pv > 0.2:
                action = "shift_load"
                reason = f"cheap hour (≤ {thr:.3f} €/kWh) with PV available"
                score = 0.60
            else:
                action = "idle"
                reason = "no action recommended"
                score = 0.30

        if cloud is not None and cloud > 80 and action in ("charge", "shift_load"):
            score = max(0.0, score - 0.10)
            reason += f" (cloudy: {cloud:.0f}%)"

        rows.append(
            {
                "timestamp": ts_dt.isoformat(),
                "action": action,
                "reason": reason,
                "score": float(min(max(score, 0.0), 1.0)),
            }
        )

    return rows
