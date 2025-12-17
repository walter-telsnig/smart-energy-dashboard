# Core recommendation logic for the Smart Energy Dashboard.
# - Loads PV, consumption, and market price CSVs
# - Applies a simple rule-based recommendation strategy
#
# Design notes:
#   SRP: pure domain/use-case logic, no HTTP or FastAPI imports
#   DIP: callable from API or other interfaces (UI, batch jobs)

from __future__ import annotations

from pathlib import Path
from typing import List, Literal, TypedDict

import pandas as pd

Action = Literal["charge", "discharge", "shift_load", "idle"]

PV_DIR = Path("infra") / "data" / "pv"
CONS_DIR = Path("infra") / "data" / "consumption"
PRICE_DIR = Path("infra") / "data" / "market"


class RecommendationRow(TypedDict):
    timestamp: str
    action: Action
    reason: str
    score: float


# ---------- data loading --------------------------------------------------------

def _load_csv(path: Path, required_cols: List[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"missing file: {path}")

    df = pd.read_csv(path)
    for c in required_cols:
        if c not in df.columns:
            raise ValueError(f"CSV '{path.name}' must contain column '{c}'")

    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    return df.sort_values("datetime").reset_index(drop=True)


def load_inputs() -> pd.DataFrame:
    """
    Load all available historical data (across years if needed).
    """
    frames = []

    for year in [2025, 2026, 2027]:
        try:
            pv = _load_csv(
                PV_DIR / f"pv_{year}_hourly.csv",
                ["datetime", "production_kw"],
            ).rename(columns={"production_kw": "pv_kw"})

            cons = _load_csv(
                CONS_DIR / f"consumption_{year}_hourly.csv",
                ["datetime", "consumption_kwh"],
            ).rename(columns={"consumption_kwh": "load_kwh"})

            price = _load_csv(
                PRICE_DIR / f"price_{year}_hourly.csv",
                ["datetime", "price_eur_mwh"],
            )

            df = pv.merge(cons, on="datetime").merge(price, on="datetime")
            frames.append(df)

        except FileNotFoundError:
            continue

    if not frames:
        raise ValueError("no historical datasets available")

    df = pd.concat(frames, ignore_index=True)

    df["pv_kwh"] = df["pv_kw"].astype(float).clip(lower=0) * 1.0
    df["price_eur_kwh"] = df["price_eur_mwh"] / 1000.0

    return df[["datetime", "pv_kwh", "load_kwh", "price_eur_kwh"]].sort_values("datetime")


# ---------- recommendation logic ------------------------------------------------

def generate_recommendations(
    *,
    hours: int,
    price_threshold_eur_kwh: float,
) -> List[RecommendationRow]:

    df = load_inputs()

    now = pd.Timestamp.utcnow().floor("H")
    today_start = now.normalize()

    history_end = today_start
    history_start = history_end - pd.Timedelta(hours=24)

    hist = df[
        (df["datetime"] >= history_start)
        & (df["datetime"] < history_end)
    ]

    if len(hist) < 24:
        raise ValueError("not enough recent history for recommendations")

    hist = hist.reset_index(drop=True)

    rows: List[RecommendationRow] = []

    for h in range(hours):
        ts = today_start + pd.Timedelta(hours=h)
        row = hist.iloc[h % 24]

        surplus = float(row["pv_kwh"]) - float(row["load_kwh"])
        price = float(row["price_eur_kwh"])

        if surplus > 0.2:
            action: Action = "charge"
            reason = f"predicted PV surplus ({surplus:.2f} kWh)"
            score = 0.85
        elif price >= price_threshold_eur_kwh and surplus < 0:
            action = "discharge"
            reason = "high price hour; avoid grid usage"
            score = 0.75
        elif price < price_threshold_eur_kwh and surplus > 0:
            action = "shift_load"
            reason = "cheap hour with PV available"
            score = 0.65
        else:
            action = "idle"
            reason = "no clear advantage"
            score = 0.30

        rows.append(
            {
                "timestamp": ts.isoformat(),
                "action": action,
                "reason": reason,
                "score": score,
            }
        )

    return rows
