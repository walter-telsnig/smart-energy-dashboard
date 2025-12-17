"""
Battery service orchestrates a greedy charge/discharge simulation for a single stream
of (PV, consumption) at hourly resolution.

Assumptions:
- timeseries has hourly steps
- production_kwh / consumption_kwh are energy-per-hour (kWh)
"""

from __future__ import annotations

from typing import List
import pandas as pd

from .domain import BatteryParams

_PV_ALIASES = [
    "production_kwh", "production_kw", "pv_kwh", "pv_kw",
    "generation_kwh", "generation_kw", "value", "production"
]
_CONS_ALIASES = ["consumption_kwh", "load_kwh", "consumption", "load", "value"]


def _pick_col(df: pd.DataFrame, candidates: list[str]) -> str:
    lower_cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand in lower_cols:
            return lower_cols[cand]
    for cand in candidates:
        if cand in df.columns:
            return cand
    return ""


def simulate(params: BatteryParams, timeseries: pd.DataFrame) -> pd.DataFrame:
    """
    Run greedy battery simulation over an hourly DataFrame with:
      - columns ['production_kwh','consumption_kwh']
      - UTC index or a datetime column already set to index by the caller
    """
    df = timeseries.copy()

    if "production_kwh" not in df.columns or "consumption_kwh" not in df.columns:
        raise ValueError("timeseries must contain columns: production_kwh, consumption_kwh")

    socs: List[float] = []
    charges: List[float] = []
    discharges: List[float] = []
    g_imports: List[float] = []
    g_exports: List[float] = []

    soc = params.initial_soc()

    for _, row in df.iterrows():
        pv = float(row["production_kwh"])
        load = float(row["consumption_kwh"])
        surplus = pv - load

        charge = discharge = g_import = g_export = 0.0

        if surplus >= 0.0:
            room_kwh = params.soc_max_kwh() - soc
            charge_gridside = min(surplus, params.p_charge_max_kw)
            charge_stored = min(room_kwh, charge_gridside * params.eta_c)
            charge = charge_stored / params.eta_c if params.eta_c > 0 else 0.0
            soc += charge_stored
            g_export = max(0.0, surplus - charge)
        else:
            need = -surplus
            available_stored = soc - params.soc_min_kwh()
            discharge_stored = min(available_stored, params.p_discharge_max_kw)
            deliverable = discharge_stored * params.eta_d
            discharge = min(need, deliverable)
            spent_stored = discharge / params.eta_d if params.eta_d > 0 else 0.0
            soc -= spent_stored
            g_import = max(0.0, need - discharge)

        soc = params.clamp_soc_kwh(soc)

        socs.append(float(soc))
        charges.append(round(charge, 6))
        discharges.append(round(discharge, 6))
        g_imports.append(round(g_import, 6))
        g_exports.append(round(g_export, 6))

    out = df.copy()
    out["soc_kwh"] = socs
    out["charge_kwh"] = charges
    out["discharge_kwh"] = discharges
    out["grid_import_kwh"] = g_imports
    out["grid_export_kwh"] = g_exports
    return out
