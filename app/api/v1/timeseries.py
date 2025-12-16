from fastapi import APIRouter, Query, HTTPException
import pandas as pd
from pathlib import Path

router = APIRouter(prefix="/timeseries", tags=["timeseries"])

def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(str(path))
    df = pd.read_csv(path)
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True)
    return df

@router.get("/merged")
def get_merged(year: int = Query(..., ge=2025, le=2027), limit: int | None = Query(None, ge=1, le=2000)):
    """
    Returns hourly merged PV + consumption + market price for the given year.
    """
    base = Path("infra/data")

    try:
        pv = _read_csv(base / "pv" / f"pv_{year}_hourly.csv").rename(columns={"production_kw": "pv_kw"})
        cons = _read_csv(base / "consumption" / f"consumption_{year}_hourly.csv").rename(columns={"consumption_kwh": "load_kwh"})
        price = _read_csv(base / "market" / f"price_{year}_hourly.csv").rename(columns={"price_eur_mwh": "price_eur_mwh"})
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Missing dataset: {e}")

    df = pv.merge(cons, on="datetime", how="inner").merge(price, on="datetime", how="inner")
    df["price_eur_kwh"] = df["price_eur_mwh"] / 1000.0
    df.drop(columns=["price_eur_mwh"], inplace=True)

    df = df.sort_values("datetime")

    if limit is not None:
        df = df.head(limit)

    return df.to_dict(orient="records")
