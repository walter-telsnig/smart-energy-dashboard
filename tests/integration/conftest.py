import pytest
from fastapi.testclient import TestClient

from infra.database import Base, engine
import infra.models

@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    # Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    # Create app per test so monkeypatching works predictably
    from app.main import create_app
    return TestClient(create_app())


@pytest.fixture(autouse=True)
def clear_open_meteo_cache():
    # Ensure Open-Meteo cache doesn't leak between tests
    try:
        from infra.weather import open_meteo
        with open_meteo._cache_lock:
            open_meteo._cache.clear()
    except Exception:
        # If module not imported yet, nothing to clear
        pass
    yield
