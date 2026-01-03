from __future__ import annotations
from pathlib import Path
import pandas as pd


def count_csv_files(folder: Path) -> int:
    if not folder.exists():
        return 0
    return len(list(folder.glob("*.csv")))


def count_csv_rows(folder: Path) -> int:
    if not folder.exists():
        return 0

    total = 0
    for csv_file in folder.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            total += len(df)
        except Exception:
            continue
    return total


def total_pv_kwh(folder: Path) -> float:
    if not folder.exists():
        return 0.0

    total_kwh = 0.0
    for csv_file in folder.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
        except Exception:
            continue

        if "production_kwh" in df.columns:
            values = pd.to_numeric(df["production_kwh"], errors="coerce")
        elif "production_kw" in df.columns:
            values = pd.to_numeric(df["production_kw"], errors="coerce") * 1.0
        else:
            continue

        total_kwh += float(values.sum())

    return total_kwh
