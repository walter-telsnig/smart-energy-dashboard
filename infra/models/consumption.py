from sqlalchemy import Column, TIMESTAMP, Float
from infra.database import Base

class Consumption(Base):
    __tablename__ = "consumption"

    datetime = Column(TIMESTAMP, primary_key=True)
    consumption_kwh = Column(Float, primary_key=False)