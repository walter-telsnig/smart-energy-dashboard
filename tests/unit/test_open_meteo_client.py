from datetime import datetime, timezone

import pandas as pd
import pytest

from infra.weather import open_meteo


def _fake_open_meteo_json():
    # Minimal valid Open-Meteo hourly payload (UTC)
    return {
        "hourly": {
            "time": [
                "2026-01-07T00:00",
                "2026-01-07T01:00",
                "2026-01-07T02:00",
                "2026-01-07T03:00",
            ],
            "temperature_2m": [1.0, 2.0, 3.0, 4.0],
            "cloud_cover": [10, 20, 30, 40],
        }
    }


def test_get_hourly_forecast_df_parses_and_filters(monkeypatch):
    def fake_fetch(*, latitude, longitude, start_date, end_date, timeout_s):
        return _fake_open_meteo_json()

    monkeypatch.setattr(open_meteo, "_fetch_open_meteo_json", fake_fetch)

    start = datetime(2026, 1, 7, 1, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 7, 3, 0, tzinfo=timezone.utc)

    df = open_meteo.get_hourly_forecast_df(
        latitude=48.2,
        longitude=16.3,
        start_dt_utc=start,
        end_dt_utc=end,
        timeout_s=1.0,
        cache_ttl_s=900,
    )

    assert list(df.columns) == ["datetime", "temp_c", "cloud_cover_pct"]
    assert len(df) == 2  # 01:00 and 02:00 (end is exclusive)
    assert df["datetime"].iloc[0] == pd.Timestamp("2026-01-07T01:00:00Z")
    assert df["temp_c"].iloc[0] == 2.0
    assert df["cloud_cover_pct"].iloc[0] == 20



def test_get_hourly_forecast_df_uses_cache(monkeypatch):
    # Ensure the test is independent of test order / prior cache population
    with open_meteo._cache_lock:
        open_meteo._cache.clear()

    calls = {"n": 0}

    def fake_fetch(*, latitude, longitude, start_date, end_date, timeout_s):
        calls["n"] += 1
        return _fake_open_meteo_json()

    monkeypatch.setattr(open_meteo, "_fetch_open_meteo_json", fake_fetch, raising=True)

    start = datetime(2026, 1, 7, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 7, 4, 0, tzinfo=timezone.utc)

    _ = open_meteo.get_hourly_forecast_df(
        latitude=48.2,
        longitude=16.3,
        start_dt_utc=start,
        end_dt_utc=end,
        timeout_s=1.0,
        cache_ttl_s=900,
    )
    _ = open_meteo.get_hourly_forecast_df(
        latitude=48.2,
        longitude=16.3,
        start_dt_utc=start,
        end_dt_utc=end,
        timeout_s=1.0,
        cache_ttl_s=900,
    )

    assert calls["n"] == 1


def test_get_hourly_forecast_df_rejects_invalid_window(monkeypatch):
    def fake_fetch(*, latitude, longitude, start_date, end_date, timeout_s):
        return _fake_open_meteo_json()

    monkeypatch.setattr(open_meteo, "_fetch_open_meteo_json", fake_fetch)

    start = datetime(2026, 1, 7, 4, 0, tzinfo=timezone.utc)
    end = datetime(2026, 1, 7, 4, 0, tzinfo=timezone.utc)

    with pytest.raises(ValueError):
        open_meteo.get_hourly_forecast_df(
            latitude=48.2,
            longitude=16.3,
            start_dt_utc=start,
            end_dt_utc=end,
            timeout_s=1.0,
            cache_ttl_s=900,
        )
