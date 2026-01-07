# core/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    # Defaults for dev; override via .env or environment variables
    db_url: str = "sqlite:///./dev.db"
    api_prefix: str = "/api/v1"
    env: str = "dev"

    demo_password: str = "changeme"

    # Weather configuration
    # "csv" keeps current behavior (hourly weather from CSV).
    # "open_meteo" enables live forecast from Open-Meteo (up to 7 days).
    weather_mode: Literal["csv", "open_meteo"] = "csv"

    # Location for weather data - Klagenfurt
    weather_lat: float = 46.6236
    weather_lon: float = 14.3075

    # Network / operational knobs
    weather_timeout_s: float = 10.0
    weather_cache_ttl_s: int = 900  # 15 min cache for forecast calls

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SED_",         # e.g. SED_DB_URL, SED_WEATHER_MODE
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()
