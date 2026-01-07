from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

from core.settings import settings
from infra.weather.open_meteo import get_hourly_forecast_df


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

        # Keep CSV-based weather in history (useful fallback/offline).
        # Live weather (Open-Meteo) will be injected later for the plan window.
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

        df["pv_kwh"] = df["pv_kw"].astype(float).clip(lower=0.0) * 1.0
        df["load_kwh"] = df["load_kwh"].astype(float).clip(lower=0.0)
        df["price_eur_kwh"] = df["price_eur_mwh"].astype(float) / 1000.0

        df["temp_c"] = pd.to_numeric(df["temp_c"], errors="coerce")
        df["cloud_cover_pct"] = pd.to_numeric(df["cloud_cover_pct"], errors="coerce")

        frames.append(df[["datetime", "pv_kwh", "load_kwh", "price_eur_kwh", "temp_c", "cloud_cover_pct"]])

    if not frames:
        raise ValueError("no historical datasets available (expected PV/consumption/price CSVs)")

    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values("datetime").reset_index(drop=True)
    return out


def window_for_today_utc(hours: int) -> TimeseriesWindow:
    if hours < 1 or hours > 168:
        raise ValueError("hours must be between 1 and 168")
    now = pd.Timestamp.utcnow()
    start = now.normalize()
    end = start + pd.Timedelta(hours=hours)
    return TimeseriesWindow(start=start, end=end)


def slice_window(df: pd.DataFrame, window: TimeseriesWindow) -> pd.DataFrame:
    out = df[(df["datetime"] >= window.start) & (df["datetime"] < window.end)].copy()
    return out.sort_values("datetime").reset_index(drop=True)


def _fallback_profile(history: pd.DataFrame, today_start: pd.Timestamp) -> pd.DataFrame:
    """
    Choose a 24-row profile to repeat:
    - prefer the 24 hours right before today_start
    - otherwise fallback to last 24 rows overall
    """
    history_end = today_start
    history_start = history_end - pd.Timedelta(hours=24)

    recent = history[(history["datetime"] >= history_start) & (history["datetime"] < history_end)].copy()
    hist = recent if len(recent) >= 24 else history.tail(24).copy()

    hist = hist.sort_values("datetime").reset_index(drop=True)
    if len(hist) < 24:
        raise ValueError("need at least 24 rows of history to build plan")
    return hist


def _inject_live_weather_if_enabled(plan: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """
    If SED_WEATHER_MODE=open_meteo, fetch hourly forecast and overwrite
    plan['temp_c'] and plan['cloud_cover_pct'] for the plan window.

    If the API call fails for any reason, keep the plan as-is (fallback to CSV/offline).
    """
    if getattr(settings, "weather_mode", "csv") != "open_meteo":
        return plan

    try:
        forecast = get_hourly_forecast_df(
            latitude=settings.weather_lat,
            longitude=settings.weather_lon,
            start_dt_utc=start.to_pydatetime(),
            end_dt_utc=end.to_pydatetime(),
            timeout_s=settings.weather_timeout_s,
            cache_ttl_s=settings.weather_cache_ttl_s,
        )
    except Exception:
        # Keep behavior non-breaking: if Open-Meteo fails, we keep whatever values exist (CSV/offline/None).
        return plan

    if forecast.empty:
        return plan

    # Merge and prefer forecast values where available
    forecast = forecast.copy()
    forecast["datetime"] = pd.to_datetime(forecast["datetime"], utc=True)

    out = plan.merge(forecast[["datetime", "temp_c", "cloud_cover_pct"]], on="datetime", how="left", suffixes=("", "_forecast"))

    # Overwrite if forecast has a value; else keep existing
    out["temp_c"] = out["temp_c_forecast"].combine_first(out["temp_c"])
    out["cloud_cover_pct"] = out["cloud_cover_pct_forecast"].combine_first(out["cloud_cover_pct"])

    out = out.drop(columns=["temp_c_forecast", "cloud_cover_pct_forecast"])
    out["temp_c"] = pd.to_numeric(out["temp_c"], errors="coerce")
    out["cloud_cover_pct"] = pd.to_numeric(out["cloud_cover_pct"], errors="coerce")

    return out


def build_today_plan(hours: int, history: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Real-data-first plan for [today 00:00 UTC, today+hours):

    - If the dataset contains those exact hours => return them directly (best case)
    - If partially missing => fill missing hours by repeating a 24h fallback profile

    Weather:
    - Default (csv): keep whatever history provides (CSV weather or None)
    - open_meteo: overwrite temp/cloud for the plan window with live forecast
    """
    if history is None:
        history = load_merged_history()
    if history.empty:
        raise ValueError("no history available")

    window = window_for_today_utc(hours)
    start = window.start
    end = window.end

    idx = pd.date_range(start, periods=hours, freq="h", tz="UTC")

    base = history.copy()
    base["datetime"] = pd.to_datetime(base["datetime"], utc=True)
    base = base.sort_values("datetime").set_index("datetime")

    plan = base.reindex(idx)[["pv_kwh", "load_kwh", "price_eur_kwh", "temp_c", "cloud_cover_pct"]].copy()

    # If everything exists, return immediately
    if plan[["pv_kwh", "load_kwh", "price_eur_kwh"]].notna().all(axis=None):
        plan = plan.reset_index().rename(columns={"index": "datetime"})
        plan = _inject_live_weather_if_enabled(plan, start, end)
        return plan

    # Fill gaps using fallback repeating pattern
    fallback = _fallback_profile(history, start)
    fb = fallback.set_index("datetime").tail(24).reset_index(drop=True)

    filled_rows = []
    for h, ts in enumerate(idx):
        row = plan.loc[ts]
        if pd.notna(row["pv_kwh"]) and pd.notna(row["load_kwh"]) and pd.notna(row["price_eur_kwh"]):
            filled_rows.append(
                {
                    "datetime": ts,
                    "pv_kwh": float(row["pv_kwh"]),
                    "load_kwh": float(row["load_kwh"]),
                    "price_eur_kwh": float(row["price_eur_kwh"]),
                    "temp_c": float(row["temp_c"]) if pd.notna(row["temp_c"]) else None,
                    "cloud_cover_pct": float(row["cloud_cover_pct"]) if pd.notna(row["cloud_cover_pct"]) else None,
                }
            )
        else:
            src = fb.iloc[h % 24]
            filled_rows.append(
                {
                    "datetime": ts,
                    "pv_kwh": float(src["pv_kwh"]),
                    "load_kwh": float(src["load_kwh"]),
                    "price_eur_kwh": float(src["price_eur_kwh"]),
                    "temp_c": float(src["temp_c"]) if pd.notna(src["temp_c"]) else None,
                    "cloud_cover_pct": float(src["cloud_cover_pct"]) if pd.notna(src["cloud_cover_pct"]) else None,
                }
            )

    out = pd.DataFrame(filled_rows)
    out["datetime"] = pd.to_datetime(out["datetime"], utc=True)

    # Finally inject live weather if enabled (overwrites temp/cloud for the whole plan window)
    out = _inject_live_weather_if_enabled(out, start, end)
    return out