import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, date, timedelta
import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your app from the correct location
from app.main import app  # ← THIS IS THE KEY IMPORT!
from infra.db import Base, get_db

# Test database
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def test_client():
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def seed_test_data(db_session):
    """Seed community test data"""
    from infra.models import Consumption, PV
    
    # Clear existing data
    db_session.query(Consumption).delete()
    db_session.query(PV).delete()
    
    # Create community consumption pattern
    test_data = []
    start_date = datetime.now() - timedelta(days=30)
    
    for i in range(30 * 24):
        dt = start_date + timedelta(hours=i)
        hour = dt.hour
        
        if 18 <= hour < 22:  # Evening peak (community pattern)
            consumption = 3.0
        else:
            consumption = 1.0
            
        test_data.append(Consumption(
            datetime=dt,
            consumption_kwh=consumption
        ))
    
    db_session.add_all(test_data)
    db_session.commit()
    
    return db_session