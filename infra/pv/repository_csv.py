from pathlib import Path
import csv
from modules.pv.ports import PVRepositoryPort
from modules.pv.domain import PVTimeSeries, PVPoint

# DIP: CSV adapter implements the PVRepositoryPort
class CSVPVRepository(PVRepositoryPort):
    def __init__(self, base_path: Path | None = None) -> None:
        if base_path is None:
            base_path = Path(__file__).resolve().parents[1] / "data" / "pv"
        self.base_path = base_path

    def load_series(self, name: str) -> PVTimeSeries:
        # Allow 'pv_2026_hourly' (without .csv) or a file name with .csv
        file_name = f"{name}.csv" if not name.endswith(".csv") else name
        path = self.base_path / file_name
        if not path.exists():
            raise FileNotFoundError(f"PV CSV not found: {path}")

        points: list[PVPoint] = []
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # expects columns: datetime, production_kw
                ts = row["datetime"]
                val = float(row["production_kw"])
                points.append(PVPoint(timestamp=ts, production_kw=val))
        return PVTimeSeries(points=points)
