from fastapi import FastAPI
from app.api.v1.accounts import router as accounts_router
from infra.db import Base, engine

def create_app() -> FastAPI:
    app = FastAPI(title="Smart Energy Dashboard API", version="0.1.0")

    # Health (useful in CI/k8s)
    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    app.include_router(accounts_router)
    return app

# Dev/CI convenience: create tables automatically.
# In production, rely on Alembic migrations only.
Base.metadata.create_all(bind=engine)

app = create_app()
