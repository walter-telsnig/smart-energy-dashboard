# app/main.py
from fastapi import FastAPI

from app.api.v1.accounts import router as accounts_router
from app.api.v1.pv import router as pv_router
from app.api.v1.timeseries import router as timeseries_router
from app.api.v1.forecast import router as forecast_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.consumption import router as consumption_router
from app.api.dataManagement.consumption import router as consumption_router_db
from app.api.dataManagement.consumption_minute import router as consumption_minute_router_db
from app.api.dataManagement.market import router as market_router_db
from app.api.dataManagement.market_minute import router as market_minute_router_db
from app.api.dataManagement.pv import router as pv_router_db
from app.api.dataManagement.weather import router as weather_router_db
from app.api.v1.market import router as market_router
from app.api.v1.battery import router as battery_router
from app.api.v1.auth import router as auth_router



def create_app() -> FastAPI:
    app = FastAPI(title="Smart Energy Dashboard API", version="0.1.0")

    @app.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    app.include_router(accounts_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(pv_router, prefix="/api/v1")
    app.include_router(timeseries_router, prefix="/api/v1")
    app.include_router(forecast_router, prefix="/api/v1")
    app.include_router(recommendations_router, prefix="/api/v1")
    app.include_router(consumption_router, prefix="/api/v1")
    app.include_router(consumption_router_db, prefix="/api/dataManagment")
    app.include_router(consumption_minute_router_db, prefix="/api/dataManagment")
    app.include_router(market_router_db, prefix="/api/dataManagment")
    app.include_router(market_minute_router_db, prefix="/api/dataManagment")
    app.include_router(pv_router_db, prefix="/api/dataManagment")
    app.include_router(weather_router_db, prefix="/api/dataManagment")
    app.include_router(market_router, prefix="/api/v1")
    app.include_router(battery_router, prefix="/api/v1")

    return app


# Dev/CI convenience: ensure tables exist for tests
# Base.metadata.create_all(bind=engine)

app = create_app()
