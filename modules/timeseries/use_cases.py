# Timeseries use-cases for the Smart Energy Dashboard.
# - Pure logic: load PV + consumption + price CSVs, merge, normalize units
# - Provides time-window slicing for "today" + horizon scenarios
#
# No FastAPI imports here.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


DATA_BASE = Path("infra") / "data"
PV_DIR = DATA_BASE / "pv"
CONS_DIR = DATA_BASE / "consumption"
PRICE_DIR = DATA_BASE / "market"


@dataclass(frozen=True)
class TimeseriesWindow:
    start: pd.Timestamp
    end: pd.Timestamp  # exclusive


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(str(path))
    df = pd.read_csv(path)
    if "datetime" not in df.columns:
        raise ValueError(f"CSV '{path.name}' must contain column 'datetime'")
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    return df


def load_merged_history(years: Iterable[int] = (2025, 2026, 2027)) -> pd.DataFrame:
    """
    Load all available PV + consumption + price data across provided years
    and return a single merged, normalized DataFrame:
      datetime, pv_kwh, load_kwh, price_eur_kwh
    """
    frames: list[pd.DataFrame] = []

    for year in years:
        pv_path = PV_DIR / f"pv_{year}_hourly.csv"
        cons_path = CONS_DIR / f"consumption_{year}_hourly.csv"
        price_path = PRICE_DIR / f"price_{year}_hourly.csv"

        if not (pv_path.exists() and cons_path.exists() and price_path.exists()):
            continue

        pv = _read_csv(pv_path)
        cons = _read_csv(cons_path)
        price = _read_csv(price_path)

        if "production_kw" not in pv.columns:
            raise ValueError(f"PV CSV '{pv_path.name}' must contain 'production_kw'")
        if "consumption_kwh" not in cons.columns:
            raise ValueError(f"Consumption CSV '{cons_path.name}' must contain 'consumption_kwh'")
        if "price_eur_mwh" not in price.columns:
            raise ValueError(f"Price CSV '{price_path.name}' must contain 'price_eur_mwh'")

        pv = pv[["datetime", "production_kw"]].rename(columns={"production_kw": "pv_kw"})
        cons = cons[["datetime", "consumption_kwh"]].rename(columns={"consumption_kwh": "load_kwh"})
        price = price[["datetime", "price_eur_mwh"]]

        df = pv.merge(cons, on="datetime", how="inner").merge(price, on="datetime", how="inner")

        # Normalize units
        df["pv_kwh"] = df["pv_kw"].astype(float).clip(lower=0.0) * 1.0  # 1h bucket
        df["price_eur_kwh"] = df["price_eur_mwh"].astype(float) / 1000.0

        frames.append(df[["datetime", "pv_kwh", "load_kwh", "price_eur_kwh"]])

    if not frames:
        raise ValueError("no historical datasets available (expected PV/consumption/price CSVs)")

    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values("datetime").reset_index(drop=True)
    return out


def window_for_today_utc(hours: int) -> TimeseriesWindow:
    """
    Default window: today 00:00 UTC -> today+hours (exclusive).
    """
    if hours < 1 or hours > 168:
        raise ValueError("hours must be between 1 and 168")
    now = pd.Timestamp.utcnow()
    start = now.normalize()  # 00:00 UTC today
    end = start + pd.Timedelta(hours=hours)
    return TimeseriesWindow(start=start, end=end)


def slice_window(df: pd.DataFrame, window: TimeseriesWindow) -> pd.DataFrame:
    """
    Slice merged df to [start, end).
    """
    out = df[(df["datetime"] >= window.start) & (df["datetime"] < window.end)].copy()
    return out.sort_values("datetime").reset_index(drop=True)

