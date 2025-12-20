# app/api/v1/consumption.py
# Consumption endpoints for the Smart Energy Dashboard.
# - Prefix is "/consumption"
# - Reads CSVs from infra/data/consumption
# - Normalizes columns to: timestamp, value
#
# Design notes:
#   SRP: this router handles HTTP + CSV loading only
#   DIP: callers depend on a stable JSON contract

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd
from pandas.api.types import is_numeric_dtype
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/consumption", tags=["consumption"])

DATA_DIR = Path("infra") / "data" / "consumption"


# ---------- helpers ------------------------------------------------------------

def _csv_path_for_key(key: str) -> Path:
    key = key.strip()
    p = (DATA_DIR / key) if key.endswith(".csv") else (DATA_DIR / f"{key}.csv")
    if not p.exists():
        candidates = {c.stem.lower(): c for c in DATA_DIR.glob("*.csv")}
        cand = candidates.get(key.lower())
        if cand is None:
            raise HTTPException(status_code=404, detail=f"series '{key}' not found")
        p = cand
    return p


def _normalize_to_timestamp_value(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["timestamp", "value"])

    lower = {str(c).lower(): c for c in df.columns}

    ts_col = (
        lower.get("timestamp")
        or lower.get("time")
        or lower.get("date")
        or lower.get("datetime")
        or df.columns[0]
    )

    numeric_cols = [c for c in df.columns if c != ts_col and is_numeric_dtype(df[c])]
    val_col = numeric_cols[0] if numeric_cols else df.columns[1]

    return df[[ts_col, val_col]].rename(
        columns={ts_col: "timestamp", val_col: "value"}
    )


def _list_csv_files() -> List[Path]:
    if not DATA_DIR.exists():
        return []
    return sorted(DATA_DIR.glob("*.csv"))


# ---------- endpoints ----------------------------------------------------------

@router.get("/catalog", response_model=dict)
def catalog() -> Dict:
    files = _list_csv_files()
    return {"items": [{"key": p.stem, "filename": p.name} for p in files]}


@router.get("/head", response_model=dict)
def head(
    key: str = Query(...),
    n: int = Query(48, ge=1, le=10_000),
) -> Dict:
    csv_path = _csv_path_for_key(key)
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    df = _normalize_to_timestamp_value(df)
    rows = df.head(n).to_dict(orient="records")
    return {"key": csv_path.stem, "count": len(rows), "rows": rows}


@router.get("", response_model=dict)
def full_series(
    key: str = Query(...),
    limit: int = Query(2000, ge=1, le=50_000),
) -> Dict:
    csv_path = _csv_path_for_key(key)
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    df = _normalize_to_timestamp_value(df)
    rows = df.head(limit).to_dict(orient="records")
    return {"key": csv_path.stem, "count": len(rows), "rows": rows}


@router.get("/range", response_model=dict)
def get_range(
    key: str = Query(..., description="CSV key"),
    start: str = Query(..., description="Start ISO datetime"),
    end: str = Query(..., description="End ISO datetime"),
) -> Dict:
    csv_path = _csv_path_for_key(key)
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    df = _normalize_to_timestamp_value(df)
    
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    
    s = pd.to_datetime(start, utc=True)
    end_dt = pd.to_datetime(end, utc=True)
    
    mask = (df["timestamp"] >= s) & (df["timestamp"] <= end_dt)
    subset = df.loc[mask]
    
    rows = subset.to_dict(orient="records")
    return {"key": csv_path.stem, "count": len(rows), "rows": rows}
