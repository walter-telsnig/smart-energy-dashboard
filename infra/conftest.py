import pytest
from infra.database import Base, engine
from infra.models import *  # registriert alle Modelle
from sqlalchemy.orm import sessionmaker
import time
from psycopg2 import OperationalError

# Optional: auf Docker-Postgres warten
def wait_for_db(timeout=30):
    start = time.time()
    while True:
        try:
            conn = engine.connect()
            conn.close()
            return
        except OperationalError:
            if time.time() - start > timeout:
                raise RuntimeError("Database not ready after 30s")
            time.sleep(1)

@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    wait_for_db()
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
