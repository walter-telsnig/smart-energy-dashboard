from sqlalchemy import Column, TIMESTAMP, Float
from infra.database import Base

class PV_Minute(Base):
    __tablename__ = "pv_minute"

    datetime = Column(TIMESTAMP, primary_key=True)
    production_kw = Column(Float, primary_key=False)