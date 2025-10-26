# app/api/v1/pv.py
# PV endpoints for the Smart Energy Dashboard.
# - Prefix is "/pv" (the API version "/api/v1" is added in app.main)
# - Reads CSVs from infra/data/pv
# - Normalizes columns to: timestamp, value  (so the UI can always plot)
# Design notes:
#   SRP: this router only handles HTTP + CSV reading logic
#   OCP: adding new sources later (DB, API) can reuse the same JSON shape
#   DIP: callers (UI) depend on the stable contract, not on CSV specifics

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pandas as pd
from pandas.api.types import is_numeric_dtype
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/pv", tags=["pv"])

# Project-relative data dir (works when started from repo root or via Docker compose)
DATA_DIR = Path("infra") / "data" / "pv"


# ---------- helpers ------------------------------------------------------------

def _csv_path_for_key(key: str) -> Path:
    """
    Accept keys with or without '.csv'. Returns a Path to an existing CSV or raises 404.
    """
    key = key.strip()
    p = (DATA_DIR / key) if key.endswith(".csv") else (DATA_DIR / f"{key}.csv")
    if not p.exists():
        # try exact match among available files (case-insensitive)
        candidates = {c.stem.lower(): c for c in DATA_DIR.glob("*.csv")}
        cand = candidates.get(key.lower())
        if cand is None:
            raise HTTPException(status_code=404, detail=f"series '{key}' not found")
        p = cand
    return p


def _normalize_to_timestamp_value(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map arbitrary CSV columns to the canonical pair: timestamp, value.
    Heuristics:
      - timestamp column: one of ["timestamp","time","date","datetime"] (case-insens.)
        else falls back to the first column.
      - value column: column literally named "value" (case-insens.) if present,
        else first numeric column that's not the timestamp,
        else second column.
    """
    if df.empty:
        return pd.DataFrame(columns=["timestamp", "value"])

    lower = {str(c).lower(): c for c in df.columns}

    # pick timestamp-like column
    ts_col = (
        lower.get("timestamp")
        or lower.get("time")
        or lower.get("date")
        or lower.get("datetime")
        or df.columns[0]
    )

    # pick value column
    if "value" in lower:
        val_col = lower["value"]
    else:
        numeric_cols = [c for c in df.columns if c != ts_col and is_numeric_dtype(df[c])]
        val_col = numeric_cols[0] if numeric_cols else (df.columns[1] if len(df.columns) > 1 else df.columns[0])

    out = df[[ts_col, val_col]].rename(columns={ts_col: "timestamp", val_col: "value"})
    return out


def _list_csv_files() -> List[Path]:
    if not DATA_DIR.exists():
        return []
    return sorted(DATA_DIR.glob("*.csv"))


def _quick_meta(p: Path) -> Dict:
    """Light metadata for catalog without loading full CSV into memory."""
    try:
        # Try to peek header to expose available columns
        header = pd.read_csv(p, nrows=0)
        cols = list(header.columns)
    except Exception:
        cols = []
    return {
        "key": p.stem,                # used by UI
        "filename": p.name,
        "path": str(p),
        "columns": cols,
    }


# ---------- endpoints ----------------------------------------------------------

@router.get("/catalog", response_model=dict)
def catalog() -> Dict:
    """
    List available PV series discovered in infra/data/pv.
    Response shape: {"items": [{"key": "...", "filename": "...", ...}, ...]}
    """
    files = _list_csv_files()
    items = [_quick_meta(p) for p in files]
    return {"items": items}


@router.get("/head", response_model=dict)
def head(
    key: str = Query(..., description="CSV key (with or without .csv)"),
    n: int = Query(48, ge=1, le=10000, description="Number of rows to return from the start"),
) -> Dict:
    """
    Return the first n rows as [{"timestamp": ..., "value": ...}, ...].
    """
    csv_path = _csv_path_for_key(key)
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"cannot read CSV '{csv_path.name}': {e}")

    df = _normalize_to_timestamp_value(df)
    rows = df.head(n).to_dict(orient="records")
    return {"key": Path(csv_path).stem, "count": len(rows), "rows": rows}


@router.get("", response_model=dict)
def full_series(
    key: str = Query(..., description="CSV key (with or without .csv)"),
    limit: int = Query(2000, ge=1, le=50_000, description="Max rows to return (guardrails for UI)"),
) -> Dict:
    """
    Return up to 'limit' rows (useful for quick analysis; for large files use paging later).
    """
    csv_path = _csv_path_for_key(key)
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"cannot read CSV '{csv_path.name}': {e}")

    df = _normalize_to_timestamp_value(df)
    rows = df.head(limit).to_dict(orient="records")
    return {"key": Path(csv_path).stem, "count": len(rows), "rows": rows}
