# modules/recommendations/use_cases.py
from __future__ import annotations

from pathlib import Path
from typing import List, Literal, TypedDict

import pandas as pd

Action = Literal["charge", "discharge", "shift_load", "idle"]

PV_DIR = Path("infra") / "data" / "pv"
CONS_DIR = Path("infra") / "data" / "consumption"
PRICE_DIR = Path("infra") / "data" / "market"

AVAILABLE_YEARS = [2025, 2026, 2027]


class RecommendationRow(TypedDict):
    timestamp: str
    action: Action
    reason: str
    score: float


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
    frames = []

    for year in AVAILABLE_YEARS:
        try:
            pv = _load_csv(PV_DIR / f"pv_{year}_hourly.csv", ["datetime", "production_kw"]).rename(
                columns={"production_kw": "pv_kw"}
            )
            cons = _load_csv(CONS_DIR / f"consumption_{year}_hourly.csv", ["datetime", "consumption_kwh"]).rename(
                columns={"consumption_kwh": "load_kwh"}
            )
            price = _load_csv(PRICE_DIR / f"price_{year}_hourly.csv", ["datetime", "price_eur_mwh"])

            df = pv.merge(cons, on="datetime").merge(price, on="datetime")
            frames.append(df)
        except FileNotFoundError:
            continue

    if not frames:
        raise ValueError("no historical datasets available")

    df = pd.concat(frames, ignore_index=True)

    df["pv_kwh"] = df["pv_kw"].astype(float).clip(lower=0) * 1.0
    df["price_eur_kwh"] = df["price_eur_mwh"].astype(float) / 1000.0

    return df[["datetime", "pv_kwh", "load_kwh", "price_eur_kwh"]].sort_values("datetime").reset_index(drop=True)


def _last_full_day_profile(df: pd.DataFrame) -> pd.DataFrame:
    """
    Latest day with a full 24h profile, returned as 24 rows (00..23).
    """
    last_dt = df["datetime"].max()
    day = last_dt.normalize()

    for _ in range(10):
        day_slice = df[(df["datetime"] >= day) & (df["datetime"] < day + pd.Timedelta(hours=24))].copy()
        if len(day_slice) >= 24:
            return day_slice.head(24).reset_index(drop=True)
        day = day - pd.Timedelta(days=1)

    raise ValueError("could not find a full 24h profile in data")


def _planning_frame(hours: int) -> pd.DataFrame:
    """
    Build a planning dataframe for 'today 00:00 -> today+hours' using the last available full-day profile.
    """
    df = load_inputs()
    profile = _last_full_day_profile(df)

    today_start = pd.Timestamp.utcnow().normalize()
    rows = []
    for h in range(hours):
        ts = today_start + pd.Timedelta(hours=h)
        src = profile.iloc[h % 24]
        rows.append(
            {
                "datetime": ts,
                "pv_kwh": float(src["pv_kwh"]),
                "load_kwh": float(src["load_kwh"]),
                "price_eur_kwh": float(src["price_eur_kwh"]),
            }
        )
    return pd.DataFrame(rows)


def generate_recommendations(*, hours: int, price_threshold_eur_kwh: float) -> List[RecommendationRow]:
    plan = _planning_frame(hours)

    rows: List[RecommendationRow] = []
    for _, r in plan.iterrows():
        ts = pd.to_datetime(r["datetime"], utc=True)
        surplus = float(r["pv_kwh"]) - float(r["load_kwh"])
        price = float(r["price_eur_kwh"])

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


# Optional but useful for cost-summary / reuse:
def build_planning_inputs(hours: int) -> pd.DataFrame:
    return _planning_frame(hours)