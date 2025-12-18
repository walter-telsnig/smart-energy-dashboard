"""
Cost model for recommendations.

v1 (simple + user-friendly):
- Baseline cost = grid_import_kwh * price
- Optimized cost (battery enabled) = run battery simulation and use simulated grid_import_kwh * price
- Export revenue is ignored by default to avoid confusing negative "cost" in PV-heavy datasets.

You can enable export revenue later when you want to model feed-in tariffs / market export.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Optional

import pandas as pd

from modules.battery.domain import BatteryParams
from modules.battery.service import simulate

ExportMode = Literal["market", "feed_in"]


@dataclass(frozen=True)
class CostParams:
    """
    v1 simplification: export revenue is OFF by default.
    """
    include_export_revenue: bool = False

    # kept for later (only used when include_export_revenue=True)
    export_mode: ExportMode = "feed_in"
    feed_in_tariff_eur_per_kwh: float = 0.08


def _validate_plan(df: pd.DataFrame) -> None:
    required = {"datetime", "pv_kwh", "load_kwh", "price_eur_kwh"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")
    if df.empty:
        raise ValueError("plan dataframe is empty")


def _baseline_flows(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["grid_import_kwh"] = (out["load_kwh"] - out["pv_kwh"]).clip(lower=0.0)
    out["grid_export_kwh"] = (out["pv_kwh"] - out["load_kwh"]).clip(lower=0.0)
    return out


def _export_revenue(flows: pd.DataFrame, params: CostParams) -> float:
    """
    Return export revenue in EUR. In v1 we typically disable this entirely.
    """
    if not params.include_export_revenue:
        return 0.0

    if params.export_mode == "market":
        return float((flows["grid_export_kwh"] * flows["price_eur_kwh"]).sum())

    # feed_in
    return float((flows["grid_export_kwh"] * params.feed_in_tariff_eur_per_kwh).sum())


def _cost_from_flows(flows: pd.DataFrame, params: CostParams) -> Dict[str, float]:
    import_cost = float((flows["grid_import_kwh"] * flows["price_eur_kwh"]).sum())
    export_revenue = _export_revenue(flows, params)

    total = import_cost - export_revenue
    return {
        "cost_eur": total,
        "import_cost_eur": import_cost,
        "export_revenue_eur": export_revenue,
        "import_kwh": float(flows["grid_import_kwh"].sum()),
        "export_kwh": float(flows["grid_export_kwh"].sum()),
    }


def compare_costs(
    plan_df: pd.DataFrame,
    *,
    battery_enabled: bool,
    battery_params: Optional[BatteryParams] = None,
    cost_params: Optional[CostParams] = None,
) -> Dict[str, float]:
    """
    Returns:
      baseline_cost_eur, recommended_cost_eur, savings_eur, ...
    """
    _validate_plan(plan_df)
    params = cost_params or CostParams()  # export revenue OFF by default

    base_flows = _baseline_flows(plan_df)
    base = _cost_from_flows(base_flows, params)

    if not battery_enabled:
        with_batt = base
    else:
        batt = battery_params or BatteryParams()

        ts = plan_df.copy()
        ts["datetime"] = pd.to_datetime(ts["datetime"], utc=True)
        ts = ts.sort_values("datetime").set_index("datetime")

        sim_in = pd.DataFrame(
            {
                "production_kwh": ts["pv_kwh"].astype(float).clip(lower=0.0),
                "consumption_kwh": ts["load_kwh"].astype(float).clip(lower=0.0),
            },
            index=ts.index,
        )

        sim_out = simulate(batt, sim_in)

        flows = pd.DataFrame(
            {
                "grid_import_kwh": sim_out["grid_import_kwh"].astype(float),
                "grid_export_kwh": sim_out["grid_export_kwh"].astype(float),
                "price_eur_kwh": ts["price_eur_kwh"].astype(float),
            },
            index=ts.index,
        )

        with_batt = _cost_from_flows(flows, params)

    return {
        "baseline_cost_eur": base["cost_eur"],
        "recommended_cost_eur": with_batt["cost_eur"],
        "savings_eur": base["cost_eur"] - with_batt["cost_eur"],
        "baseline_import_kwh": base["import_kwh"],
        "baseline_export_kwh": base["export_kwh"],
        "recommended_import_kwh": with_batt["import_kwh"],
        "recommended_export_kwh": with_batt["export_kwh"],
    }
