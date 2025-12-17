# Timeseries use-cases for the Smart Energy Dashboard.
# - Pure logic: load PV + consumption + price (+ weather) CSVs, merge, normalize units
# - Provides time-window slicing for "today" + horizon scenarios
#
# No FastAPI imports here.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


DATA_BASE = Path("infra") / "data"
PV_DIR = DATA_BASE / "pv"
CONS_DIR = DATA_BASE / "consumption"
PRICE_DIR = DATA_BASE / "market"
WEATHER_DIR = DATA_BASE / "weather"


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
    Load all available PV + consumption + price (+ weather) data across provided years
    and return a single merged, normalized DataFrame:

      datetime, pv_kwh, load_kwh, price_eur_kwh, temp_c, cloud_cover_pct

    Weather is optional:
      - if weather CSVs exist, merge them on datetime (inner)
      - if missing, keep columns but fill as NA
    """
    frames: list[pd.DataFrame] = []

    for year in years:
        pv_path = PV_DIR / f"pv_{year}_hourly.csv"
        cons_path = CONS_DIR / f"consumption_{year}_hourly.csv"
        price_path = PRICE_DIR / f"price_{year}_hourly.csv"
        weather_path = WEATHER_DIR / f"weather_{year}_hourly.csv"

        if not (pv_path.exists() and cons_path.exists() and price_path.exists()):
            continue

        pv = _read_csv(pv_path)
        cons = _read_csv(cons_path)
        price = _read_csv(price_path)

        # Validate required columns
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

        # Optional weather merge
        if weather_path.exists():
            weather = _read_csv(weather_path)
            for col in ["temp_c", "cloud_cover_pct"]:
                if col not in weather.columns:
                    raise ValueError(f"Weather CSV '{weather_path.name}' must contain '{col}'")
            weather = weather[["datetime", "temp_c", "cloud_cover_pct"]]
            df = df.merge(weather, on="datetime", how="inner")
        else:
            df["temp_c"] = pd.NA
            df["cloud_cover_pct"] = pd.NA

        # Normalize units
        df["pv_kwh"] = df["pv_kw"].astype(float).clip(lower=0.0) * 1.0  # 1h bucket
        df["load_kwh"] = df["load_kwh"].astype(float).clip(lower=0.0)
        df["price_eur_kwh"] = df["price_eur_mwh"].astype(float) / 1000.0

        # Ensure numeric where possible (weather may be NA)
        if "temp_c" in df.columns:
            df["temp_c"] = pd.to_numeric(df["temp_c"], errors="coerce")
        if "cloud_cover_pct" in df.columns:
            df["cloud_cover_pct"] = pd.to_numeric(df["cloud_cover_pct"], errors="coerce")

        frames.append(df[["datetime", "pv_kwh", "load_kwh", "price_eur_kwh", "temp_c", "cloud_cover_pct"]])

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


def build_today_plan(hours: int, history: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Build a planning dataframe for 'today 00:00 -> today+hours' by repeating a 24h pattern.

    Strategy:
    - Prefer the 24 hours right before today's 00:00 UTC (history slice)
    - If not enough rows (synthetic / gaps), fall back to last 24 rows overall
    - Repeat the 24h pattern to fill `hours`

    Output columns (stable):
      datetime, pv_kwh, load_kwh, price_eur_kwh, temp_c, cloud_cover_pct
    """
    if history is None:
        history = load_merged_history()

    if history.empty:
        raise ValueError("no history available")

    window = window_for_today_utc(hours)
    today_start = window.start

    history_end = today_start
    history_start = history_end - pd.Timedelta(hours=24)
    recent = history[(history["datetime"] >= history_start) & (history["datetime"] < history_end)].copy()
    hist = recent if len(recent) >= 24 else history.tail(24).copy()

    hist = hist.sort_values("datetime").reset_index(drop=True)
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
                "temp_c": float(src["temp_c"]) if pd.notna(src["temp_c"]) else None,
                "cloud_cover_pct": float(src["cloud_cover_pct"]) if pd.notna(src["cloud_cover_pct"]) else None,
            }
        )

    return pd.DataFrame(rows)
