from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, date
from threading import Lock
from time import monotonic
from typing import Any, Dict, Optional, Tuple

import httpx
import pandas as pd


OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"

# We keep the variable names aligned with your existing code expectations.
# - temperature_2m -> temp_c
# - cloud_cover    -> cloud_cover_pct
_HOURLY_VARS = ("temperature_2m", "cloud_cover")


@dataclass(frozen=True)
class OpenMeteoQueryKey:
    latitude: float
    longitude: float
    start_date: date
    end_date: date
    hourly_vars: Tuple[str, ...]


# Simple in-memory cache to avoid re-fetching on frequent UI refreshes
_cache: Dict[OpenMeteoQueryKey, Tuple[float, pd.DataFrame]] = {}
_cache_lock = Lock()


def _to_utc(dt: datetime) -> datetime:
    """Return dt as timezone-aware UTC datetime."""
    if dt.tzinfo is None:
        # Treat naive datetimes as UTC (consistent with your current UTC-based planning).
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _get_cache(key: OpenMeteoQueryKey, ttl_s: int) -> Optional[pd.DataFrame]:
    if ttl_s <= 0:
        return None
    now = monotonic()
    with _cache_lock:
        item = _cache.get(key)
        if not item:
            return None
        ts, df = item
        if (now - ts) > ttl_s:
            _cache.pop(key, None)
            return None
        return df.copy()


def _set_cache(key: OpenMeteoQueryKey, df: pd.DataFrame) -> None:
    with _cache_lock:
        _cache[key] = (monotonic(), df.copy())


def _fetch_open_meteo_json(
    *,
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
    timeout_s: float,
) -> Dict[str, Any]:
    """
    Fetch Open-Meteo forecast JSON.
    Note: Open-Meteo uses date-based start/end for forecast windows; we filter to exact datetime range later.
    """
    params: dict[str, str | int | float | bool | None] = {
        "latitude": float(latitude),
        "longitude": float(longitude),
        "hourly": ",".join(_HOURLY_VARS),
        "timezone": "UTC",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }

    try:
        with httpx.Client(timeout=timeout_s) as client:
            resp = client.get(OPEN_METEO_BASE_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, dict):
                raise RuntimeError("Open-Meteo response JSON is not an object.")
            return data
    except httpx.HTTPError as e:
        raise RuntimeError(f"Open-Meteo request failed: {e}") from e


def get_hourly_forecast_df(
    *,
    latitude: float,
    longitude: float,
    start_dt_utc: datetime,
    end_dt_utc: datetime,
    timeout_s: float = 10.0,
    cache_ttl_s: int = 900,
) -> pd.DataFrame:
    """
    Return hourly forecast data as a DataFrame with columns:
      - datetime (UTC, tz-aware)
      - temp_c
      - cloud_cover_pct

    The returned DataFrame is filtered to:
      start_dt_utc <= datetime < end_dt_utc

    Notes:
    - Open-Meteo returns hourly arrays for the requested date range.
    - We request by date and then filter to the exact datetime window.
    """
    start_dt_utc = _to_utc(start_dt_utc)
    end_dt_utc = _to_utc(end_dt_utc)

    if end_dt_utc <= start_dt_utc:
        raise ValueError("end_dt_utc must be after start_dt_utc")

    # Open-Meteo uses date window; include both dates, then filter precisely.
    start_d = start_dt_utc.date()
    end_d = end_dt_utc.date()

    key = OpenMeteoQueryKey(
        latitude=round(float(latitude), 6),
        longitude=round(float(longitude), 6),
        start_date=start_d,
        end_date=end_d,
        hourly_vars=_HOURLY_VARS,
    )

    cached = _get_cache(key, cache_ttl_s)
    if cached is not None:
        return _filter_window(cached, start_dt_utc, end_dt_utc)

    data = _fetch_open_meteo_json(
        latitude=float(latitude),
        longitude=float(longitude),
        start_date=start_d,
        end_date=end_d,
        timeout_s=float(timeout_s),
    )

    df = _parse_open_meteo_hourly(data)
    _set_cache(key, df)
    return _filter_window(df, start_dt_utc, end_dt_utc)


def _parse_open_meteo_hourly(data: Dict[str, Any]) -> pd.DataFrame:
    hourly = data.get("hourly")
    if not isinstance(hourly, dict):
        raise RuntimeError("Open-Meteo response missing 'hourly' object.")

    times = hourly.get("time")
    temps = hourly.get("temperature_2m")
    clouds = hourly.get("cloud_cover")

    if not isinstance(times, list):
        raise RuntimeError("Open-Meteo hourly response missing 'time' list.")
    if not isinstance(temps, list):
        raise RuntimeError("Open-Meteo hourly response missing 'temperature_2m' list.")
    if not isinstance(clouds, list):
        raise RuntimeError("Open-Meteo hourly response missing 'cloud_cover' list.")

    if not (len(times) == len(temps) == len(clouds)):
        raise RuntimeError("Open-Meteo hourly lists are not the same length.")

    # Open-Meteo time strings are like "2026-01-07T00:00"
    dt = pd.to_datetime(times, utc=True, errors="coerce")
    if dt.isna().any():
        raise RuntimeError("Failed to parse some Open-Meteo hourly timestamps.")

    df = pd.DataFrame(
        {
            "datetime": dt,
            "temp_c": pd.to_numeric(temps, errors="coerce"),
            "cloud_cover_pct": pd.to_numeric(clouds, errors="coerce"),
        }
    )

    # Keep it tidy and predictable
    df = df.dropna(subset=["datetime"]).sort_values("datetime").reset_index(drop=True)

    # Clamp cloud cover to [0, 100] if present; keep NaNs if any.
    if "cloud_cover_pct" in df.columns:
        df["cloud_cover_pct"] = df["cloud_cover_pct"].clip(lower=0, upper=100)

    return df


def _filter_window(df: pd.DataFrame, start_dt_utc: datetime, end_dt_utc: datetime) -> pd.DataFrame:
    """Filter df to the [start, end) window."""
    if df.empty:
        return df

    start_ts = pd.Timestamp(start_dt_utc)
    end_ts = pd.Timestamp(end_dt_utc)

    out = df[(df["datetime"] >= start_ts) & (df["datetime"] < end_ts)].copy()
    out = out.sort_values("datetime").reset_index(drop=True)
    return out
