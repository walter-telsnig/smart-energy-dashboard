# app/main.py
from fastapi import FastAPI

from app.api.v1.accounts import router as accounts_router
from app.api.v1.pv import router as pv_router

# IMPORTANT: import models BEFORE create_all so tables are known to SQLAlchemy
from modules.accounts.model import Account  # noqa: F401
from app.api.v1.auth import router as auth_router

from infra.db import Base, engine

def create_app() -> FastAPI:
    app = FastAPI(title="Smart Energy Dashboard API", version="0.1.0")

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    # add version ONCE here
    app.include_router(accounts_router, prefix="/api/v1")
    app.include_router(pv_router,       prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    return app

# Dev/CI convenience: ensure tables exist for tests
Base.metadata.create_all(bind=engine)

app = create_app()