import pytest
from fastapi.testclient import TestClient
from app.main import create_app
from infra.database import Base, engine
import infra.models  # noqa: F401

print(">>> conftest loaded <<<")

@pytest.fixture(scope="session")
def client():
    app = create_app()
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    print(">>> before create_all <<<")
    Base.metadata.create_all(bind=engine)
    print(">>> after create_all <<<")
    yield
    print(">>> before dispose <<<")
    engine.dispose()
    print(">>> after dispose <<<")
    #Base.metadata.drop_all(bind=engine)