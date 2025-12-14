from __future__ import annotations
from pathlib import Path
from ui.utils.overview_metrics import count_csv_files, count_csv_rows, total_pv_kwh


def write_text(p: Path, text: str) -> None:
    p.write_text(text, encoding="utf-8")


def test_count_csv_files(tmp_path: Path) -> None:
    # Arrange: create 2 CSV files and 1 non-CSV
    write_text(tmp_path / "a.csv", "x,y\n1,2\n")
    write_text(tmp_path / "b.csv", "x,y\n3,4\n")
    write_text(tmp_path / "note.txt", "hello")

    # Act
    n = count_csv_files(tmp_path)

    # Assert
    assert n == 2


def test_count_csv_rows(tmp_path: Path) -> None:
    # a.csv has 2 data rows, b.csv has 1 data row
    write_text(tmp_path / "a.csv", "c1\n10\n20\n")
    write_text(tmp_path / "b.csv", "c1\n30\n")

    assert count_csv_rows(tmp_path) == 3


def test_total_pv_kwh_from_production_kwh(tmp_path: Path) -> None:
    write_text(
        tmp_path / "pv.csv",
        "datetime,production_kwh\n"
        "2025-01-01 00:00:00+00:00,1.5\n"
        "2025-01-01 01:00:00+00:00,2.0\n",
    )

    assert total_pv_kwh(tmp_path) == 3.5


def test_total_pv_kwh_from_production_kw(tmp_path: Path) -> None:
    # hourly kW -> kWh conversion (kW * 1h)
    write_text(
        tmp_path / "pv.csv",
        "datetime,production_kw\n"
        "2025-01-01 00:00:00+00:00,1.0\n"
        "2025-01-01 01:00:00+00:00,2.0\n",
    )

    assert total_pv_kwh(tmp_path) == 3.0
