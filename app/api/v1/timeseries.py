from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from modules.timeseries.use_cases import build_today_plan

router = APIRouter(prefix="/timeseries", tags=["timeseries"])


@router.get("/merged")
def get_merged(
    window: bool = Query(True, description="If true, return a planning window from today's 00:00 UTC"),
    hours: int = Query(24, ge=1, le=168, description="Planning horizon in hours from today's 00:00 UTC"),
):
    """
    Stable output columns:
      datetime, pv_kwh, load_kwh, price_eur_kwh, temp_c, cloud_cover_pct
    """
    try:
        if not window:
            # for now, keep API simple: UI always uses window mode
            raise ValueError("Only window=true is supported in v1")

        plan = build_today_plan(hours=hours)

        # JSON-friendly
        plan["datetime"] = pd.to_datetime(plan["datetime"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        return plan.to_dict(orient="records")

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Missing dataset: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
