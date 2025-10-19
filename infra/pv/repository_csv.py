from pathlib import Path
import csv
from typing import List
from modules.pv.ports import PVRepositoryPort
from modules.pv.domain import PVTimeSeries, PVPoint

class CSVPVRepository(PVRepositoryPort):
    def __init__(self, base_path: Path | None = None) -> None:
        if base_path is None:
            base_path = Path(__file__).resolve().parents[1] / "data" / "pv"
        self.base_path = base_path

    def _resolve(self, name: str) -> Path:
        file_name = f"{name}.csv" if not name.endswith(".csv") else name
        return self.base_path / file_name

    def load_series(self, name: str) -> PVTimeSeries:
        path = self._resolve(name)
        if not path.exists():
            raise FileNotFoundError(f"PV CSV not found: {path}")

        points: list[PVPoint] = []
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                points.append(PVPoint(timestamp=row["datetime"], production_kw=float(row["production_kw"])))
        return PVTimeSeries(points=points)

    def list_series(self) -> List[str]:
        # Return stems without ".csv", e.g., ["pv_2026_hourly", ...]
        if not self.base_path.exists():
            return []
        return sorted(p.stem for p in self.base_path.glob("*.csv"))

    def head(self, name: str, n: int) -> PVTimeSeries:
        """Efficiently read only the first n rows after header."""
        path = self._resolve(name)
        if not path.exists():
            raise FileNotFoundError(f"PV CSV not found: {path}")

        points: list[PVPoint] = []
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= n:
                    break
                points.append(PVPoint(timestamp=row["datetime"], production_kw=float(row["production_kw"])))
        return PVTimeSeries(points=points)

    def quick_metadata(self, name: str) -> dict:
        """Return minimal metadata: rows count and first/last timestamps (single pass)."""
        path = self._resolve(name)
        if not path.exists():
            raise FileNotFoundError(f"PV CSV not found: {path}")

        first_ts = last_ts = None
        count = 0
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ts = row["datetime"]
                if first_ts is None:
                    first_ts = ts
                last_ts = ts
                count += 1
        return {"key": path.stem, "rows": count, "from": first_ts, "to": last_ts}
