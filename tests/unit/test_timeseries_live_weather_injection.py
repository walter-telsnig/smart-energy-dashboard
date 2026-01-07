from datetime import datetime, timezone

import pandas as pd

from core.settings import settings
from modules.timeseries import use_cases


def _make_history_24h(start_utc: str = "2026-01-07T00:00:00Z") -> pd.DataFrame:
    idx = pd.date_range(pd.Timestamp(start_utc), periods=24, freq="h", tz="UTC")
    return pd.DataFrame(
        {
            "datetime": idx,
            "pv_kwh": [1.0] * 24,
            "load_kwh": [2.0] * 24,
            "price_eur_kwh": [0.3] * 24,
            "temp_c": [None] * 24,
            "cloud_cover_pct": [None] * 24,
        }
    )


def test_build_today_plan_overwrites_weather_when_open_meteo_enabled(monkeypatch):
    # Enable Open-Meteo in settings for this test
    monkeypatch.setattr(settings, "weather_mode", "open_meteo", raising=False)
    monkeypatch.setattr(settings, "weather_lat", 48.2, raising=False)
    monkeypatch.setattr(settings, "weather_lon", 16.3, raising=False)
    monkeypatch.setattr(settings, "weather_timeout_s", 1.0, raising=False)
    monkeypatch.setattr(settings, "weather_cache_ttl_s", 0, raising=False)

    def fake_forecast(*, latitude, longitude, start_dt_utc, end_dt_utc, timeout_s, cache_ttl_s):
        dt = pd.date_range(pd.Timestamp(start_dt_utc), periods=24, freq="h", tz="UTC")
        return pd.DataFrame(
            {
                "datetime": dt,
                "temp_c": [10.0] * 24,
                "cloud_cover_pct": [55.0] * 24,
            }
        )

    monkeypatch.setattr(use_cases, "get_hourly_forecast_df", fake_forecast)

    history = _make_history_24h()
    plan = use_cases.build_today_plan(hours=24, history=history)

    assert "temp_c" in plan.columns
    assert "cloud_cover_pct" in plan.columns
    assert float(plan["temp_c"].iloc[0]) == 10.0
    assert float(plan["cloud_cover_pct"].iloc[0]) == 55.0


def test_build_today_plan_keeps_existing_weather_on_open_meteo_failure(monkeypatch):
    monkeypatch.setattr(settings, "weather_mode", "open_meteo", raising=False)

    def failing_forecast(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(use_cases, "get_hourly_forecast_df", failing_forecast)

    history = _make_history_24h()
    # Provide some existing weather to prove it remains
    history["temp_c"] = [1.0] * 24
    history["cloud_cover_pct"] = [20.0] * 24

    plan = use_cases.build_today_plan(hours=24, history=history)

    assert float(plan["temp_c"].iloc[0]) == 1.0
    assert float(plan["cloud_cover_pct"].iloc[0]) == 20.0
