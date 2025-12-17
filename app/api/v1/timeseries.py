from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from modules.timeseries.use_cases import build_today_plan, load_merged_history

router = APIRouter(prefix="/timeseries", tags=["timeseries"])


@router.get("/merged")
def get_merged(
    window: bool = Query(
        True,
        description="If true, returns a planning window starting at today's 00:00 UTC. "
        "Kept for compatibility with the Streamlit UI.",
    ),
    hours: int = Query(24, ge=1, le=168, description="Planning horizon in hours from today's 00:00 UTC"),
):
    """
    Returns hourly merged PV + consumption + market price (+ weather) for a planning horizon.

    Output columns (stable):
    - datetime
    - pv_kwh
    - load_kwh
    - price_eur_kwh
    - temp_c
    - cloud_cover_pct
    """
    try:
        history = load_merged_history()

        if window:
            plan = build_today_plan(hours=hours, history=history)
        else:
            # If someone wants a raw history slice, return the latest `hours` rows (still normalized).
            plan = history.tail(hours).copy()

        # JSON-friendly datetime
        plan["datetime"] = pd.to_datetime(plan["datetime"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        return plan.to_dict(orient="records")

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Missing dataset: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))