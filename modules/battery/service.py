# modules/battery/service.py
"""
Battery service orchestrates a greedy charge/discharge simulation for a single stream
of (PV, consumption) at hourly resolution.

- mypy-friendly vectorized assignment (avoid df.at[...] inside loop)
- Accepts PV column aliases incl. 'production_kw' and converts to kWh (hourly).
"""

from __future__ import annotations
from typing import List
import pandas as pd
from .domain import BatteryParams

_PV_ALIASES = ["production_kwh", "production_kw", "pv_kwh", "pv_kw", "generation_kwh", "generation_kw", "value", "production"]
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

def _load_series(pv_csv: str, cons_csv: str, start: str, end: str) -> pd.DataFrame:
    """
    Load and align PV and consumption series.

    PV CSV can have power (kW) or energy (kWh). If power column found, it is converted to kWh
    assuming hourly resolution (kW * 1h).
    Expects time column 'datetime' (UTC).
    """
    idx = pd.date_range(pd.Timestamp(start), pd.Timestamp(end), freq="H", inclusive="left", tz="UTC")

    def _read_csv_auto(path: str, aliases: list[str], to_name: str, convert_kw_to_kwh: bool = False) -> pd.Series:
        df = pd.read_csv(path)
        if "datetime" not in df.columns:
            raise KeyError(f"CSV '{path}' must contain a 'datetime' column.")
        ts = pd.to_datetime(df["datetime"], utc=True)
        col = _pick_col(df, aliases)
        if not col:
            raise KeyError(f"Could not find any of {aliases} in '{path}'. Columns: {list(df.columns)}")
        s = pd.Series(df[col].values, index=ts).reindex(idx).interpolate(limit_direction="both")
        if convert_kw_to_kwh and col.lower().endswith("_kw"):
            s = s.astype("float64") * 1.0  # hourly step ⇒ kW * 1h = kWh
        return s.rename(to_name)

    pv = _read_csv_auto(pv_csv, _PV_ALIASES, "production_kwh", convert_kw_to_kwh=True)
    load = _read_csv_auto(cons_csv, _CONS_ALIASES, "consumption_kwh", convert_kw_to_kwh=False)

    out = pd.concat([pv, load], axis=1)
    return out

def simulate(params: BatteryParams, timeseries: pd.DataFrame) -> pd.DataFrame:
    """
    Run greedy battery simulation over an hourly DataFrame
    with columns ['production_kwh','consumption_kwh'] and UTC index.
    """
    df = timeseries.copy()

    # Prepare storage for mypy-friendly, vectorized assignment after loop after build-and-test error
    socs: List[float] = []
    charges: List[float] = []
    discharges: List[float] = []
    g_imports: List[float] = []
    g_exports: List[float] = []

    soc = params.capacity_kwh * params.soc_min  # start at minimum

    for _, row in df.iterrows():
        pv = float(row["production_kwh"])
        load = float(row["consumption_kwh"])
        surplus = pv - load

        charge = discharge = g_import = g_export = 0.0

        if surplus >= 0.0:
            room_kwh = params.capacity_kwh * params.soc_max - soc
            charge_gridside = min(surplus, params.p_charge_max_kw)
            charge_stored = min(room_kwh, charge_gridside * params.eta_c)
            charge = charge_stored / params.eta_c if params.eta_c > 0 else 0.0
            soc += charge_stored
            g_export = max(0.0, surplus - charge)
        else:
            need = -surplus
            available_stored = soc - params.capacity_kwh * params.soc_min
            discharge_stored = min(available_stored, params.p_discharge_max_kw)
            deliverable = discharge_stored * params.eta_d
            discharge = min(need, deliverable)
            spent_stored = discharge / params.eta_d if params.eta_d > 0 else 0.0
            soc -= spent_stored
            g_import = max(0.0, need - discharge)

        soc = params.clamp_soc(soc)

        socs.append(soc)
        charges.append(round(charge, 6))
        discharges.append(round(discharge, 6))
        g_imports.append(round(g_import, 6))
        g_exports.append(round(g_export, 6))

    df = df.copy()
    df["soc_kwh"] = socs
    df["charge_kwh"] = charges
    df["discharge_kwh"] = discharges
    df["grid_import_kwh"] = g_imports
    df["grid_export_kwh"] = g_exports
    return df

def load_price(price_csv: str, start: str, end: str) -> pd.Series:
    """Load price series and align to hourly window. Expects 'datetime', 'price_eur_mwh'."""
    idx = pd.date_range(pd.Timestamp(start), pd.Timestamp(end), freq="H", inclusive="left", tz="UTC")
    df = pd.read_csv(price_csv)
    ts = pd.to_datetime(df["datetime"], utc=True)
    s = pd.Series(df["price_eur_mwh"].values, index=ts)
    s = s.reindex(idx).ffill().bfill()  # mypy-friendly
    return s

def compute_costs(
    sim: pd.DataFrame,
    price: pd.Series,
    export_mode: str = "feed_in",
    feed_in_tariff_eur_per_kwh: float = 0.08,
) -> pd.DataFrame:
    """
    Attach cost columns to a simulation frame.
    - import_cost_eur = grid_import_kwh * (price_eur_mwh / 1000)
    - export_revenue_eur = grid_export_kwh * (price_eur_mwh / 1000) if export_mode=='market'
                           else grid_export_kwh * feed_in_tariff_eur_per_kwh
    - net_cost_eur = import_cost_eur - export_revenue_eur
    """
    df = sim.join(price.rename("price_eur_mwh"), how="left").ffill().bfill()
    df["import_cost_eur"] = df["grid_import_kwh"] * (df["price_eur_mwh"] / 1000.0)
    if export_mode == "market":
        df["export_revenue_eur"] = df["grid_export_kwh"] * (df["price_eur_mwh"] / 1000.0)
    else:
        df["export_revenue_eur"] = df["grid_export_kwh"] * float(feed_in_tariff_eur_per_kwh)
    df["net_cost_eur"] = df["import_cost_eur"] - df["export_revenue_eur"]
    return df
