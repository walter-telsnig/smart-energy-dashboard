# modules/battery/service.py
"""
Battery service orchestrates a greedy charge/discharge simulation for a single stream
of (PV, consumption) at hourly resolution.

Key fixes:
- soc_min / soc_max are fractions (0..1), but SoC is tracked in kWh
- clamp uses BatteryParams.clamp_soc_kwh()
- simulation starts at BatteryParams.initial_soc()
- public load_series() wrapper (avoid depending on private _load_series in APIs)
"""

from __future__ import annotations

from typing import List

import pandas as pd

from .domain import BatteryParams

_PV_ALIASES = [
    "production_kwh",
    "production_kw",
    "pv_kwh",
    "pv_kw",
    "generation_kwh",
    "generation_kw",
    "value",
    "production",
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


def _load_series(pv_csv: str, cons_csv: str, start: str, end: str) -> pd.DataFrame:
    """
    Load and align PV and consumption series.

    PV CSV can have power (kW) or energy (kWh). If a *_kw column is found, it is converted
    to kWh assuming hourly resolution (kW * 1h).

    Expects time column 'datetime' (UTC).
    Output columns:
      - production_kwh
      - consumption_kwh
    Index: hourly UTC datetimes in [start, end).
    """
    idx = pd.date_range(
        pd.Timestamp(start),
        pd.Timestamp(end),
        freq="H",
        inclusive="left",
        tz="UTC",
    )

    def _read_csv_auto(
        path: str,
        aliases: list[str],
        to_name: str,
        convert_kw_to_kwh: bool = False,
    ) -> pd.Series:
        df = pd.read_csv(path)
        if "datetime" not in df.columns:
            raise KeyError(f"CSV '{path}' must contain a 'datetime' column.")
        ts = pd.to_datetime(df["datetime"], utc=True)

        col = _pick_col(df, aliases)
        if not col:
            raise KeyError(f"Could not find any of {aliases} in '{path}'. Columns: {list(df.columns)}")

        s = pd.Series(df[col].values, index=ts).reindex(idx).interpolate(limit_direction="both")

        # Convert hourly power to energy if the chosen column is clearly kW
        if convert_kw_to_kwh and col.lower().endswith("_kw"):
            s = s.astype("float64") * 1.0

        return s.rename(to_name)

    pv = _read_csv_auto(pv_csv, _PV_ALIASES, "production_kwh", convert_kw_to_kwh=True)
    load = _read_csv_auto(cons_csv, _CONS_ALIASES, "consumption_kwh", convert_kw_to_kwh=False)

    out = pd.concat([pv, load], axis=1)
    out.index.name = "datetime"
    return out


def load_series(pv_csv: str, cons_csv: str, start: str, end: str) -> pd.DataFrame:
    """
    Public wrapper around _load_series. Use THIS from API layers.
    """
    return _load_series(pv_csv, cons_csv, start, end)


def simulate(params: BatteryParams, timeseries: pd.DataFrame) -> pd.DataFrame:
    """
    Run greedy battery simulation over an hourly DataFrame
    with columns ['production_kwh','consumption_kwh'] and UTC datetime index.

    Output adds:
      soc_kwh, charge_kwh, discharge_kwh, grid_import_kwh, grid_export_kwh
    """
    df = timeseries.copy()

    required_cols = {"production_kwh", "consumption_kwh"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"simulate() missing columns: {sorted(missing)}")

    socs: List[float] = []
    charges: List[float] = []
    discharges: List[float] = []
    g_imports: List[float] = []
    g_exports: List[float] = []

    # Start SoC (kWh), clamped to [soc_min_kwh, soc_max_kwh]
    soc = params.initial_soc()

    soc_min = params.soc_min_kwh()
    soc_max = params.soc_max_kwh()

    for _, row in df.iterrows():
        pv = float(row["production_kwh"])
        load = float(row["consumption_kwh"])
        surplus = pv - load

        charge = discharge = g_import = g_export = 0.0

        if surplus >= 0.0:
            # Charge from PV surplus
            room_kwh = max(0.0, soc_max - soc)

            # max energy we can pull this hour on the AC/DC side (kWh for 1h step)
            charge_gridside_kwh = min(surplus, float(params.p_charge_max_kw))

            # stored energy after charge efficiency
            charge_stored_kwh = min(room_kwh, charge_gridside_kwh * float(params.eta_c))

            # energy taken from PV surplus to achieve that stored energy
            charge = charge_stored_kwh / float(params.eta_c) if params.eta_c > 0 else 0.0

            soc += charge_stored_kwh
            g_export = max(0.0, surplus - charge)

        else:
            # Need energy: discharge battery if possible
            need_kwh = -surplus
            available_stored_kwh = max(0.0, soc - soc_min)

            discharge_stored_kwh = min(available_stored_kwh, float(params.p_discharge_max_kw))
            deliverable_kwh = discharge_stored_kwh * float(params.eta_d)

            discharge = min(need_kwh, deliverable_kwh)

            spent_stored_kwh = discharge / float(params.eta_d) if params.eta_d > 0 else 0.0
            soc -= spent_stored_kwh

            g_import = max(0.0, need_kwh - discharge)

        soc = params.clamp_soc_kwh(soc)

        socs.append(soc)
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


def load_price(price_csv: str, start: str, end: str) -> pd.Series:
    """
    Load price series and align to hourly window.
    Expects columns: 'datetime', 'price_eur_mwh'.
    Returns EUR/MWh aligned to [start, end) hourly UTC.
    """
    idx = pd.date_range(pd.Timestamp(start), pd.Timestamp(end), freq="H", inclusive="left", tz="UTC")

    df = pd.read_csv(price_csv)
    if "datetime" not in df.columns or "price_eur_mwh" not in df.columns:
        raise KeyError("Price CSV must contain columns ['datetime','price_eur_mwh']")

    ts = pd.to_datetime(df["datetime"], utc=True)
    s = pd.Series(df["price_eur_mwh"].values, index=ts).reindex(idx).ffill().bfill()
    s.name = "price_eur_mwh"
    return s


def compute_costs(
    sim: pd.DataFrame,
    price_eur_mwh: pd.Series,
    *,
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
    df = sim.join(price_eur_mwh.rename("price_eur_mwh"), how="left").ffill().bfill()

    df["import_cost_eur"] = df["grid_import_kwh"] * (df["price_eur_mwh"] / 1000.0)

    if export_mode == "market":
        df["export_revenue_eur"] = df["grid_export_kwh"] * (df["price_eur_mwh"] / 1000.0)
    else:
        df["export_revenue_eur"] = df["grid_export_kwh"] * float(feed_in_tariff_eur_per_kwh)

    df["net_cost_eur"] = df["import_cost_eur"] - df["export_revenue_eur"]
    return df
