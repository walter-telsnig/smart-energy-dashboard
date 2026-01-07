import pandas as pd
from core.settings import settings
from modules.timeseries import use_cases


def test_build_today_plan_early_return_branch(monkeypatch):
    # ensure open meteo doesn't interfere
    monkeypatch.setattr(settings, "weather_mode", "csv", raising=False)

    # Create history covering today window fully
    window = use_cases.window_for_today_utc(24)
    idx = pd.date_range(window.start, periods=24, freq="h", tz="UTC")

    history = pd.DataFrame(
        {
            "datetime": idx,
            "pv_kwh": [1.0] * 24,
            "load_kwh": [2.0] * 24,
            "price_eur_kwh": [0.3] * 24,
            "temp_c": [5.0] * 24,
            "cloud_cover_pct": [25.0] * 24,
        }
    )

    plan = use_cases.build_today_plan(hours=24, history=history)
    assert len(plan) == 24
    assert plan["pv_kwh"].notna().all()
    assert plan["load_kwh"].notna().all()
    assert plan["price_eur_kwh"].notna().all()


def test_build_today_plan_fallback_branch(monkeypatch):
    monkeypatch.setattr(settings, "weather_mode", "csv", raising=False)

    window = use_cases.window_for_today_utc(24)
    idx = pd.date_range(window.start, periods=24, freq="h", tz="UTC")

    # Only provide 10 rows in the window -> forces fallback for missing
    partial = pd.DataFrame(
        {
            "datetime": idx[:10],
            "pv_kwh": [1.0] * 10,
            "load_kwh": [2.0] * 10,
            "price_eur_kwh": [0.3] * 10,
            "temp_c": [None] * 10,
            "cloud_cover_pct": [None] * 10,
        }
    )

    # Provide at least 24 fallback rows overall
    fb_idx = pd.date_range(window.start - pd.Timedelta(hours=24), periods=24, freq="h", tz="UTC")
    fallback_hist = pd.DataFrame(
        {
            "datetime": fb_idx,
            "pv_kwh": [9.0] * 24,
            "load_kwh": [8.0] * 24,
            "price_eur_kwh": [0.7] * 24,
            "temp_c": [1.0] * 24,
            "cloud_cover_pct": [50.0] * 24,
        }
    )

    history = pd.concat([fallback_hist, partial], ignore_index=True)
    plan = use_cases.build_today_plan(hours=24, history=history)

    assert len(plan) == 24
    # the missing tail should be filled with fallback values
    assert float(plan["pv_kwh"].iloc[-1]) == 9.0
    assert float(plan["load_kwh"].iloc[-1]) == 8.0
