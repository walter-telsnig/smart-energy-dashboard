from pydantic import BaseModel
import os

class Settings(BaseModel):
    # Central place to read configuration (12-factor). SRP.
    db_url: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

settings = Settings()
