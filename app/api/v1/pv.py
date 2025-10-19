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
    try:
        series: PVTimeSeries = repo.load_series(key)
        return {"points": [p.__dict__ for p in series.points]}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/head", response_model=dict)
def get_pv_head(
    key: str = Query("pv_2026_hourly", description="CSV key/filename without extension"),
    n: int = Query(48, ge=1, le=8760, description="Number of points to return"),
    repo: CSVPVRepository = Depends(get_repo),
):
    """Return the first n points (useful for UI prototyping)."""
    try:
        series: PVTimeSeries = repo.head(key, n)
        return {"points": [p.__dict__ for p in series.points], "count": len(series.points)}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/catalog", response_model=dict)
def list_available_series(repo: CSVPVRepository = Depends(get_repo)):
    """
    List available PV series keys (derived from CSV filenames).
    Also include lightweight metadata for each series.
    """
    keys = repo.list_series()
    meta = []
    for k in keys:
        try:
            meta.append(repo.quick_metadata(k))
        except FileNotFoundError:
            # ignore mid-air deletions
            continue
    return {"series": meta}
