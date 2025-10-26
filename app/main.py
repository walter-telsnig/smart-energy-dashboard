# app/main.py
from fastapi import FastAPI
from app.api.v1.accounts import router as accounts_router
from app.api.v1.pv import router as pv_router
from infra.db import Base, engine

def create_app() -> FastAPI:
    app = FastAPI(title="Smart Energy Dashboard API", version="0.1.0")

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    # Mount all v1 endpoints under /api/v1
    app.include_router(accounts_router, prefix="/api/v1", tags=["accounts"])
    app.include_router(pv_router,       prefix="/api/v1", tags=["pv"])
    return app

# Dev/CI convenience
Base.metadata.create_all(bind=engine)

app = create_app()
