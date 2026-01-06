"""
Improved Locust test plan for Smart Energy Dashboard

Goals:
- Produce actionable endpoint-level latency metrics (p50/p95/p99)
- Validate correctness (status + basic content checks) so performance numbers are meaningful
- Provide a realistic "user-like" load pattern but configurable for capacity tests

Usage examples:
  # Realistic baseline (human-like think time)
  locust -f locustfile.py --headless -u 10 -r 2 --run-time 1m --host http://localhost:8000

  # More aggressive (reduce think time via env vars)
  set LOCUST_WAIT_MIN=0.1
  set LOCUST_WAIT_MAX=0.3
  locust -f locustfile.py --headless -u 25 -r 5 --run-time 2m --host http://localhost:8000

Optional env vars:
  PV_KEY=pv_2025_hourly
  PV_HEAD_N=48
  PV_LIMIT=100
  LOCUST_WAIT_MIN=1
  LOCUST_WAIT_MAX=3
"""

from __future__ import annotations

import os
import random
from typing import Any

from locust import HttpUser, task, between


def _env_float(name: str, default: float) -> float:
    """Read float env var safely."""
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    """Read int env var safely."""
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


class SmartEnergyUser(HttpUser):
    """
    User behavior model:
    - Majority of traffic is "read" endpoints (PV catalog/head/full)
    - Some lightweight health checks
    - Think time is configurable to simulate human behavior or push capacity
    """

    # Configurable think time
    _wait_min = _env_float("LOCUST_WAIT_MIN", 1.0)
    _wait_max = _env_float("LOCUST_WAIT_MAX", 3.0)
    wait_time = between(_wait_min, _wait_max)

    # Configurable dataset and limits
    pv_key = os.getenv("PV_KEY", "pv_2025_hourly")
    pv_head_n = _env_int("PV_HEAD_N", 48)
    pv_limit = _env_int("PV_LIMIT", 100)

    def on_start(self) -> None:
        """
        Optional warm-up per user.
        Keep this lightweight, otherwise you distort early percentiles.
        """
        # Warm-up: one health check to ensure the service is reachable.
        # (We don't mark this as failure if it fails; Locust will show it anyway.)
        self.client.get("/health", name="GET /health (warmup)")

    # ----------------------------
    # Helper methods (keeps tasks clean)
    # ----------------------------

    def _validate_json(self, resp, expected_type: type | None = None) -> Any:
        """Try to parse JSON and optionally validate top-level type."""
        try:
            data = resp.json()
        except Exception:
            return None

        if expected_type is not None and not isinstance(data, expected_type):
            return None
        return data

    # ----------------------------
    # Tasks
    # ----------------------------

    @task(1)
    def health_check(self) -> None:
        """Lightweight liveness-style endpoint. Should be very fast and stable."""
        with self.client.get("/health", name="GET /health", catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"Unexpected status: {r.status_code}")

    @task(2)
    def get_pv_catalog(self) -> None:
        """Fetch list of available PV datasets."""
        with self.client.get("/api/v1/pv/catalog", name="GET /pv/catalog", catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"Unexpected status: {r.status_code}")
                return

            # Basic correctness check: JSON should be list/dict (depending on your API shape)
            data = self._validate_json(r)
            if data is None:
                r.failure("Response is not valid JSON")
                return

            if not isinstance(data, (list, dict)):
                r.failure(f"Unexpected JSON type: {type(data).__name__}")

    @task(3)
    def get_pv_head(self) -> None:
        """Fetch the first N rows of a dataset."""
        path = f"/api/v1/pv/head?key={self.pv_key}&n={self.pv_head_n}"
        with self.client.get(path, name="GET /pv/head", catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"Unexpected status: {r.status_code}")
                return

            data = self._validate_json(r)
            if data is None:
                r.failure("Response is not valid JSON")
                return

    @task(3)
    def get_pv_full(self) -> None:
        """Fetch a limited amount of PV time-series data (heavier than /head)."""
        path = f"/api/v1/pv?key={self.pv_key}&limit={self.pv_limit}"
        with self.client.get(path, name="GET /pv (full)", catch_response=True) as r:
            if r.status_code != 200:
                r.failure(f"Unexpected status: {r.status_code}")
                return

            data = self._validate_json(r)
            if data is None:
                r.failure("Response is not valid JSON")
                return

    @task(1)
    def realistic_user_flow(self) -> None:
        """
        Optional: a mini 'journey' to mimic how a dashboard behaves.
        Kept low weight to not dominate endpoint-level metrics.
        """
        # Randomize the order slightly (more realistic access pattern)
        steps = ["catalog", "head", "full"]
        random.shuffle(steps)

        for step in steps:
            if step == "catalog":
                self.get_pv_catalog()
            elif step == "head":
                self.get_pv_head()
            elif step == "full":
                self.get_pv_full()
