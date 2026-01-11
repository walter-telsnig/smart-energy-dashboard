# tests/integration/conftest.py
from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient


def pytest_configure(config):
    # avoids "UnknownMarkWarning" when you start adding marks
    config.addinivalue_line("markers", "db: tests that require a running Postgres database")


@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    """
    Only create tables when DB tests are explicitly enabled.
    Run DB tests with:
      PowerShell: $env:RUN_DB_TESTS="1"; pytest -q tests/integration -m db
      cmd.exe:    set RUN_DB_TESTS=1 && pytest -q tests/integration -m db
    """
    if os.getenv("RUN_DB_TESTS", "0") != "1":
        
        yield
        return

    from infra.database import Base, engine

    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    # Optional cleanup (usually off to avoid deleting dev DB):
    # Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    from app.main import create_app
    return TestClient(create_app())


@pytest.fixture(autouse=True)
def clear_open_meteo_cache():
    try:
        from infra.weather import open_meteo
        with open_meteo._cache_lock:
            open_meteo._cache.clear()
    except Exception:
        pass
    yield
