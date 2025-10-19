from fastapi import APIRouter, Depends, HTTPException, Query
from infra.pv.repository_csv import CSVPVRepository
from modules.pv.domain import PVTimeSeries

router = APIRouter(prefix="/api/v1/pv", tags=["pv"])

def get_repo():
    return CSVPVRepository()

@router.get("/", response_model=dict)
def get_pv_series(
    key: str = Query("pv_2026_hourly", description="CSV key/filename without extension"),
    repo: CSVPVRepository = Depends(get_repo),
):
    """
    Returns a PV time series as JSON (for UI consumption).
    Example: /api/v1/pv?key=pv_2026_hourly
    Response: { "points": [ { "timestamp": "...", "production_kw": 12.3 }, ... ] }
    """
    try:
        series: PVTimeSeries = repo.load_series(key)
        # Return a plain dict (pydantic-free here) for lightness
        return {"points": [p.__dict__ for p in series.points]}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
