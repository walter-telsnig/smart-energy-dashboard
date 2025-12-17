# modules/forecast/use_cases.py
# Forecast use-cases for the Smart Energy Dashboard.
# - Encapsulates all forecasting logic
# - No FastAPI, no HTTP, no framework dependencies
#
# Design notes:
#   SRP: pure forecasting logic only
#   DIP: API layer depends on this module, never the other way around

from __future__ import annotations

from pathlib import Path
from typing import List

import pandas as pd

PV_DIR = Path("infra") / "data" / "pv"


# ---------- helpers -------------------------------------------------------------

def _pv_csv_path(year: int, key_template: str) -> Path:
    key = key_template.format(year=year).strip()
    path = PV_DIR / f"{key}.csv"
    if not path.exists():
        raise FileNotFoundError(f"PV series not found: {path}")
    return path


def load_pv_series(year: int, key_template: str) -> pd.DataFrame:
    """
    Load PV CSV and normalize to: datetime, pv_kwh
    """
    path = _pv_csv_path(year, key_template)
    df = pd.read_csv(path)

    if "datetime" not in df.columns or "production_kw" not in df.columns:
        raise ValueError(
            f"PV CSV '{path.name}' must contain columns: datetime, production_kw"
        )

    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    df = df.sort_values("datetime").reset_index(drop=True)

    # kW for 1 hour → kWh
    df["pv_kwh"] = df["production_kw"].astype(float).clip(lower=0) * 1.0
    return df[["datetime", "pv_kwh"]]


def baseline_next_hours(df: pd.DataFrame, hours: int) -> pd.DataFrame:
    """
    Baseline forecast:
    Repeat the last 24-hour PV profile for the next N hours.
    """
    if df.empty:
        raise ValueError("no data available for forecasting")

    history = df.tail(24)
    if len(history) < 24:
        raise ValueError("need at least 24 rows for baseline forecast")

    last_ts = df["datetime"].iloc[-1]
    values = history["pv_kwh"].tolist()

    rows = []
    for h in range(hours):
        ts = last_ts + pd.Timedelta(hours=h + 1)
        rows.append((ts, float(values[h % 24])))

    return pd.DataFrame(rows, columns=["datetime", "value"])


def forecast_next(
    *,
    year: int,
    hours: int,
    key_template: str,
) -> list[dict]:
    """
    Return a baseline PV forecast as plain dicts:
    [{"timestamp": str, "value": float}, ...]
    """
    key = key_template.format(year=year)
    path = PV_DIR / f"{key}.csv"
    if not path.exists():
        raise FileNotFoundError(f"PV series not found: {path}")

    df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    df = df.sort_values("datetime").reset_index(drop=True)

    if len(df) < 24:
        raise ValueError("need at least 24 rows for baseline forecast")

    history = df.tail(24)
    last_ts = history["datetime"].iloc[-1]
    values = history["production_kw"].astype(float).clip(lower=0).values

    rows = []
    for h in range(hours):
        ts = last_ts + pd.Timedelta(hours=h + 1)
        rows.append(
            {
                "timestamp": ts.isoformat(),
                "value": float(values[h % 24]),
            }
        )

    return rows



def train_baseline(years: List[int], key_template: str) -> int:
    """
    Placeholder training use-case.
    Returns how many rows would be used for training.
    """
    frames = [load_pv_series(y, key_template) for y in years]
    df = pd.concat(frames, ignore_index=True)
    return int(len(df))
