#!/usr/bin/env python3
"""
Import PV and Consumption CSVs into the SQL database (defaults to sqlite ./dev.db).

Usage:
  python scripts/import_csv_to_db.py --consumption infra/data/consumption/consumption.csv --pv infra/data/pv/pv.csv

By default this will create the tables (if not present) and upsert rows by primary key (datetime).
Use --drop to drop & recreate the tables before importing.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import logging

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

from infra.db import engine, SessionLocal, Base

# Import module models (these register with Base via infra.db.Base)
from modules.consumption.model import Consumption as ConsumptionModel
from modules.pv.model import PV as PVModel

logger = logging.getLogger("import_csv_to_db")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def _read_and_validate(path: Path, required_cols: list[str]) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    df = pd.read_csv(path)
    lower_cols = {c.lower(): c for c in df.columns}
    for col in required_cols:
        if col not in lower_cols:
            raise ValueError(f"CSV '{path.name}' must contain column '{col}' (found: {list(df.columns)})")
    # Normalize column names to expected case
    df = df.rename(columns={lower_cols[c]: c for c in lower_cols})
    return df


def _to_dt(val):
    return pd.to_datetime(val, utc=True).to_pydatetime()


def import_consumption(session, csv_path: Path) -> int:
    df = _read_and_validate(csv_path, ["datetime", "consumption_kwh"])
    count = 0
    for _, r in df.iterrows():
        try:
            ts = _to_dt(r["datetime"])
            val = float(r["consumption_kwh"])
        except Exception as e:
            logger.warning("Skipping row due to parse error: %s", e)
            continue
        obj = ConsumptionModel(datetime=ts, consumption_kwh=val)
        session.merge(obj)
        count += 1
    session.commit()
    return count


def import_pv(session, csv_path: Path) -> int:
    df = _read_and_validate(csv_path, ["datetime", "production_kw"])
    count = 0
    for _, r in df.iterrows():
        try:
            ts = _to_dt(r["datetime"])
            val = float(r["production_kw"])
        except Exception as e:
            logger.warning("Skipping row due to parse error: %s", e)
            continue
        obj = PVModel(datetime=ts, production_kw=val)
        session.merge(obj)
        count += 1
    session.commit()
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--consumption", type=Path, default=Path("infra/data/consumption/consumption.csv"), help="Path to consumption CSV")
    parser.add_argument("--pv", type=Path, default=Path("infra/data/pv/pv.csv"), help="Path to pv CSV")
    parser.add_argument("--drop", action="store_true", help="Drop and recreate tables before import")

    args = parser.parse_args(argv)

    # Ensure ORM tables are created
    if args.drop:
        logger.info("Dropping all tables (if any)")
        Base.metadata.drop_all(bind=engine)

    logger.info("Creating tables (if not exist)")
    Base.metadata.create_all(bind=engine)

    # Open DB session
    session = SessionLocal()
    try:
        if args.consumption:
            logger.info("Importing consumption from %s", args.consumption)
            n = import_consumption(session, Path(args.consumption))
            logger.info("Imported %d consumption rows", n)

        if args.pv:
            logger.info("Importing PV from %s", args.pv)
            n = import_pv(session, Path(args.pv))
            logger.info("Imported %d PV rows", n)

    except (FileNotFoundError, ValueError) as e:
        logger.error("Failed: %s", e)
        return 2
    except SQLAlchemyError as e:
        logger.error("DB error: %s", e)
        return 3
    finally:
        session.close()

    logger.info("Done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
