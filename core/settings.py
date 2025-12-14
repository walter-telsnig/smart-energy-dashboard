# core/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Defaults for dev; override via .env or environment variables
    db_url: str = "sqlite:///./dev.db"
    api_prefix: str = "/api/v1"
    env: str = "dev"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SED_",         # e.g. SED_DB_URL
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()
