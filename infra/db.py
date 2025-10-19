# Infra: DB setup. Keeps technology concerns at the edge. SRP (infra only).
# ADP: Higher layers do not import engine creation code—dependencies point inward.

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from core.settings import settings

engine = create_engine(
    settings.db_url,
    future=True,
    echo=False,
    connect_args={"check_same_thread": False} if settings.db_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()
