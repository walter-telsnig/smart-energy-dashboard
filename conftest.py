import pytest
from infra.database import Base, engine
import infra.models  # noqa: F401

@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    #Base.metadata.drop_all(bind=engine)