from sqlalchemy import Column, TIMESTAMP, Float
from infra.database import Base

class Market_Minute(Base):
    __tablename__ = "market_minute"

    datetime = Column(TIMESTAMP, primary_key=True)
    price_eur_mwh = Column(Float, primary_key=False)