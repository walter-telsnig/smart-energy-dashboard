# infra/db.py
# Infra: DB setup. Keeps technology concerns at the edge. SRP (infra only).
# ADP: Higher layers do not import engine creation code—dependencies point inward.

from typing import Iterator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from core.settings import settings

# --- Engine ---
engine = create_engine(
    settings.db_url,
    future=True,
    echo=False,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if settings.db_url.startswith("sqlite") else {},
)

# --- Session factory ---
# Note: class_=Session helps type checkers (SessionLocal() -> Session)
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    future=True,
    class_=Session,
)

# --- Declarative base for ORM models ---
Base = declarative_base()

# --- FastAPI dependency for DB session ---
def get_db() -> Iterator[Session]:
    """
    Yields a SQLAlchemy Session and ensures proper close.
    Usage:
        from fastapi import Depends
        from sqlalchemy.orm import Session
        from infra.db import get_db

        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
