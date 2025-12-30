from sqlalchemy import Column, TIMESTAMP, Float
from infra.database import Base

class PV(Base):
    __tablename__ = "pv"

    datetime = Column(TIMESTAMP, primary_key=True)
    production_kw = Column(Float, primary_key=False)