from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/timeseries", tags=["timeseries"])

BASE = Path("infra") / "data"
PV_DIR = BASE / "pv"
CONS_DIR = BASE / "consumption"
PRICE_DIR = BASE / "market"


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(str(path))
    df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    return df


def _load_all_years() -> pd.DataFrame:
    """
    Load and merge PV + consumption + price across all available years.
    Normalizes output columns to: datetime, pv_kwh, load_kwh, price_eur_kwh
    """
    frames: List[pd.DataFrame] = []

    for year in (2025, 2026, 2027):
        pv_path = PV_DIR / f"pv_{year}_hourly.csv"
        cons_path = CONS_DIR / f"consumption_{year}_hourly.csv"
        price_path = PRICE_DIR / f"price_{year}_hourly.csv"

        if not (pv_path.exists() and cons_path.exists() and price_path.exists()):
            continue

        pv = _read_csv(pv_path).rename(columns={"production_kw": "pv_kw"})
        cons = _read_csv(cons_path).rename(columns={"consumption_kwh": "load_kwh"})
        price = _read_csv(price_path)  # keep price_eur_mwh

        # Validate required columns early (clear error messages)
        for col in ["datetime", "pv_kw"]:
            if col not in pv.columns:
                raise ValueError(f"{pv_path.name} missing column '{col}'")
        for col in ["datetime", "load_kwh"]:
            if col not in cons.columns:
                raise ValueError(f"{cons_path.name} missing column '{col}'")
        for col in ["datetime", "price_eur_mwh"]:
            if col not in price.columns:
                raise ValueError(f"{price_path.name} missing column '{col}'")

        df = pv.merge(cons[["datetime", "load_kwh"]], on="datetime", how="inner").merge(
            price[["datetime", "price_eur_mwh"]], on="datetime", how="inner"
        )

        df["pv_kwh"] = df["pv_kw"].astype(float).clip(lower=0) * 1.0  # 1h bucket
        df["load_kwh"] = df["load_kwh"].astype(float).clip(lower=0)
        df["price_eur_kwh"] = df["price_eur_mwh"].astype(float) / 1000.0

        frames.append(df[["datetime", "pv_kwh", "load_kwh", "price_eur_kwh"]])

    if not frames:
        raise ValueError("no historical datasets available (pv/consumption/price)")

    out = pd.concat(frames, ignore_index=True)
    return out.sort_values("datetime").reset_index(drop=True)


def _build_plan_from_last24(history_df: pd.DataFrame, hours: int, today_start: pd.Timestamp) -> pd.DataFrame:
    """
    Create a 'plan' for the next N hours by repeating the last-24h pattern.
    Returned datetimes are anchored to today_start (real time), not dataset time.
    """
    if history_df.empty:
        raise ValueError("no history available")

    # Use the last 24 rows available (robust if exact today_start slice is missing)
    hist = history_df.tail(24).reset_index(drop=True)
    if len(hist) < 24:
        raise ValueError("need at least 24 rows of history to build plan")

    rows = []
    for h in range(hours):
        ts = today_start + pd.Timedelta(hours=h)
        src = hist.iloc[h % 24]
        rows.append(
            {
                "datetime": ts,
                "pv_kwh": float(src["pv_kwh"]),
                "load_kwh": float(src["load_kwh"]),
                "price_eur_kwh": float(src["price_eur_kwh"]),
            }
        )

    return pd.DataFrame(rows)


@router.get("/merged")
def get_merged(
    hours: int = Query(24, ge=1, le=168, description="Planning horizon in hours from today's 00:00 UTC"),
):
    """
    Returns hourly merged PV + consumption + market price for a planning horizon:
    - Starts at today's 00:00 (UTC)
    - Extends for `hours` (up to 1 week)
    - Uses last-24h pattern from the historical datasets as a simple baseline projection

    Output columns (stable):
    - datetime
    - pv_kwh
    - load_kwh
    - price_eur_kwh
    """
    try:
        df = _load_all_years()

        now = pd.Timestamp.utcnow().floor("h")
        today_start = now.normalize()

        # Prefer history right before today_start; fallback handled by tail(24) anyway
        history_end = today_start
        history_start = history_end - pd.Timedelta(hours=24)
        recent = df[(df["datetime"] >= history_start) & (df["datetime"] < history_end)]

        # If the slice is incomplete (common in synthetic datasets), fallback to last 24 overall
        history_df = recent if len(recent) >= 24 else df

        plan = _build_plan_from_last24(history_df, hours=hours, today_start=today_start)

        # Return as JSON-friendly
        plan["datetime"] = plan["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        return plan.to_dict(orient="records")

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Missing dataset: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
