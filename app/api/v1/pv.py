# app/api/v1/pv.py
from fastapi import APIRouter, Depends, HTTPException, Query
from infra.pv.repository_csv import CSVPVRepository
from modules.pv.domain import PVTimeSeries

# IMPORTANT: versioning is handled in app.main include_router(prefix="/api/v1")
router = APIRouter(prefix="/pv", tags=["pv"])

def get_repo():
    return CSVPVRepository()

@router.get("", response_model=dict)
def get_pv_series(
    key: str = Query("pv_2026_hourly", description="CSV key/filename without extension"),
    repo: CSVPVRepository = Depends(get_repo),
):
    """
    Returns the full series. Responds with both 'rows' and 'points'
    for backward-compatibility (UI can use either).
    """
    try:
        series: PVTimeSeries = repo.load_series(key)
        rows = [p.__dict__ for p in series.points]
        return {"rows": rows, "points": rows, "count": len(rows), "key": key}
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
        rows = [p.__dict__ for p in series.points]
        return {"rows": rows, "points": rows, "count": len(rows), "key": key}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/catalog", response_model=dict)
def list_available_series(repo: CSVPVRepository = Depends(get_repo)):
    """
    List available PV series keys (derived from CSV filenames) with light metadata.
    Returns 'items' (for UI) and 'series' (for older code) pointing to the same list.
    Each item should contain at least a 'key'.
    """
    keys = repo.list_series()  # e.g. ["pv_2025_hourly", "pv_2026_hourly", ...]
    meta = []
    for k in keys:
        try:
            m = repo.quick_metadata(k)  # expect dict; ensure it includes 'key'
            if "key" not in m:
                m["key"] = k
            meta.append(m)
        except FileNotFoundError:
            continue
    return {"items": meta, "series": meta}
