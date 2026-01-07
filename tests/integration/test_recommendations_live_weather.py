import pandas as pd

from core.settings import settings
from modules.timeseries import use_cases


def test_recommendations_endpoint_works_with_open_meteo_enabled(client, monkeypatch):
    # Enable Open-Meteo
    monkeypatch.setattr(settings, "weather_mode", "open_meteo", raising=False)

    # Mock forecast so no network call happens
    def fake_forecast(*, latitude, longitude, start_dt_utc, end_dt_utc, timeout_s, cache_ttl_s):
        # Match the requested plan window length approximately by building hourly range
        dt = pd.date_range(pd.Timestamp(start_dt_utc), pd.Timestamp(end_dt_utc), freq="h", tz="UTC", inclusive="left")
        return pd.DataFrame(
            {
                "datetime": dt,
                "temp_c": [12.0] * len(dt),
                "cloud_cover_pct": [10.0] * len(dt),
            }
        )

    monkeypatch.setattr(use_cases, "get_hourly_forecast_df", fake_forecast)

    resp = client.get("/api/v1/recommendations")
    assert resp.status_code == 200

    data = resp.json()
    assert "rows" in data
    assert isinstance(data["rows"], list)
    assert len(data["rows"]) > 0

    row = data["rows"][0]
    assert "timestamp" in row
    assert "action" in row
    assert "reason" in row
    assert "score" in row
