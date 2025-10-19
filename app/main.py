from fastapi import FastAPI
from app.api.v1.accounts import router as accounts_router
from app.api.v1.pv import router as pv_router
from infra.db import Base, engine

def create_app() -> FastAPI:
    app = FastAPI(title="Smart Energy Dashboard API", version="0.1.0")

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    app.include_router(accounts_router)
    app.include_router(pv_router)  # ← add PV endpoints
    return app

Base.metadata.create_all(bind=engine)  # dev/CI convenience
app = create_app()
