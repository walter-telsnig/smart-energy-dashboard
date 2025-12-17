# Cost model for the Smart Energy Dashboard.
# - Pure Python / pandas (no FastAPI)
# - Computes "with recommendations vs without" cost KPIs
#
# Assumptions (v1):
# - 1 row = 1 hour
# - PV/load are energy in kWh for that hour
# - price is €/kWh for that hour
# - export earns feed_in_factor * price (defaults to 0.0 = no compensation)
#
# Recommendation actions affect grid interaction in a simple, transparent way:
# - baseline: grid_import = max(load - pv, 0), export = max(pv - load, 0)
# - with actions:
#     charge     -> reduces export by charging battery using PV surplus (up to available export)
#     discharge  -> reduces import by discharging battery (up to import)
#     shift_load -> shifts a fraction of import away from expensive hours toward cheaper ones (simplified)
#     idle       -> no change
#
# This is intentionally simple and deterministic for a demo-ready KPI.

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Literal, Optional

import pandas as pd

Action = Literal["charge", "discharge", "shift_load", "idle"]


@dataclass(frozen=True)
class CostModelParams:
    """
    Tunable parameters for v1 cost model.
    """
    feed_in_factor: float = 0.0          # revenue = export_kwh * price * feed_in_factor
    charge_capture: float = 1.0          # fraction of PV export captured when action=="charge"
    discharge_offset: float = 1.0        # fraction of import offset when action=="discharge"
    shift_fraction: float = 0.2          # fraction of import reduced when action=="shift_load"


def validate_input_df(df: pd.DataFrame) -> None:
    required = {"datetime", "pv_kwh", "load_kwh", "price_eur_kwh"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"missing required columns: {sorted(missing)}")

    if df.empty:
        raise ValueError("input df is empty")

    # basic sanity
    for col in ["pv_kwh", "load_kwh", "price_eur_kwh"]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(f"column '{col}' must be numeric")


def validate_recommendations_df(reco: pd.DataFrame) -> None:
    required = {"timestamp", "action"}
    missing = required - set(reco.columns)
    if missing:
        raise ValueError(f"recommendations missing columns: {sorted(missing)}")


def baseline_grid_flows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute baseline import/export kWh per hour.
    """
    out = df.copy()
    out["grid_import_kwh"] = (out["load_kwh"] - out["pv_kwh"]).clip(lower=0.0)
    out["grid_export_kwh"] = (out["pv_kwh"] - out["load_kwh"]).clip(lower=0.0)
    return out


def baseline_cost(df: pd.DataFrame, params: CostModelParams) -> Dict[str, float]:
    """
    Baseline: pay for imports, optionally earn for exports.
    """
    flows = baseline_grid_flows(df)

    import_cost = float((flows["grid_import_kwh"] * flows["price_eur_kwh"]).sum())
    export_revenue = float((flows["grid_export_kwh"] * flows["price_eur_kwh"] * params.feed_in_factor).sum())

    total = import_cost - export_revenue
    return {
        "cost_eur": total,
        "import_cost_eur": import_cost,
        "export_revenue_eur": export_revenue,
        "import_kwh": float(flows["grid_import_kwh"].sum()),
        "export_kwh": float(flows["grid_export_kwh"].sum()),
    }


def apply_recommendations(
    df: pd.DataFrame,
    recommendations: pd.DataFrame,
    params: CostModelParams,
) -> pd.DataFrame:
    """
    Apply recommendations on top of baseline flows.

    Strategy (v1):
    - Merge recommendations by hour (timestamp aligned to df.datetime)
    - Modify grid_import_kwh / grid_export_kwh based on action
      (no explicit battery SoC yet; purely local adjustment)
    """
    validate_input_df(df)
    validate_recommendations_df(recommendations)

    base = baseline_grid_flows(df)
    reco = recommendations.copy()

    # Normalize timestamps
    reco["timestamp"] = pd.to_datetime(reco["timestamp"], utc=True)
    base["datetime"] = pd.to_datetime(base["datetime"], utc=True)

    merged = base.merge(
        reco[["timestamp", "action"]],
        left_on="datetime",
        right_on="timestamp",
        how="left",
    )
    merged.drop(columns=["timestamp"], inplace=True)
    merged["action"] = merged["action"].fillna("idle")

    # Ensure floats
    merged["grid_import_kwh"] = merged["grid_import_kwh"].astype(float)
    merged["grid_export_kwh"] = merged["grid_export_kwh"].astype(float)

    # Apply actions
    def _apply_row(row: pd.Series) -> pd.Series:
        action: Action = row["action"]  # type: ignore[assignment]
        imp = float(row["grid_import_kwh"])
        exp = float(row["grid_export_kwh"])

        if action == "charge":
            # capture some export into battery (reduces export)
            captured = min(exp, exp * params.charge_capture)
            exp = exp - captured

        elif action == "discharge":
            # offset some import by discharging battery (reduces import)
            offset = min(imp, imp * params.discharge_offset)
            imp = imp - offset

        elif action == "shift_load":
            # simplistic: reduce import by shift_fraction (assumes moved elsewhere)
            reduced = min(imp, imp * params.shift_fraction)
            imp = imp - reduced

        # idle -> unchanged
        row["grid_import_kwh"] = imp
        row["grid_export_kwh"] = exp
        return row

    merged = merged.apply(_apply_row, axis=1)

    return merged


def cost_with_recommendations(
    df: pd.DataFrame,
    recommendations: pd.DataFrame,
    params: CostModelParams,
) -> Dict[str, float]:
    """
    Cost under the modified grid flows.
    """
    merged = apply_recommendations(df, recommendations, params)

    import_cost = float((merged["grid_import_kwh"] * merged["price_eur_kwh"]).sum())
    export_revenue = float((merged["grid_export_kwh"] * merged["price_eur_kwh"] * params.feed_in_factor).sum())
    total = import_cost - export_revenue

    return {
        "cost_eur": total,
        "import_cost_eur": import_cost,
        "export_revenue_eur": export_revenue,
        "import_kwh": float(merged["grid_import_kwh"].sum()),
        "export_kwh": float(merged["grid_export_kwh"].sum()),
    }


def compare_costs(
    df: pd.DataFrame,
    recommendations: pd.DataFrame,
    params: Optional[CostModelParams] = None,
) -> Dict[str, float]:
    """
    Return a compact KPI dict: baseline vs with_recommendations.
    """
    params = params or CostModelParams()

    base = baseline_cost(df, params)
    with_rec = cost_with_recommendations(df, recommendations, params)

    return {
        "baseline_cost_eur": base["cost_eur"],
        "recommended_cost_eur": with_rec["cost_eur"],
        "savings_eur": base["cost_eur"] - with_rec["cost_eur"],
        "baseline_import_kwh": base["import_kwh"],
        "baseline_export_kwh": base["export_kwh"],
        "recommended_import_kwh": with_rec["import_kwh"],
        "recommended_export_kwh": with_rec["export_kwh"],
    }
