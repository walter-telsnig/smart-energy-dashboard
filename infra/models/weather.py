from sqlalchemy import Column, TIMESTAMP, Float
from infra.database import Base

class Weather(Base):
    __tablename__ = "weather"

    datetime = Column(TIMESTAMP, primary_key=True)
    temp_c = Column(Float, primary_key=False)
    cloud_cover_pct = Column(Float, primary_key=False)