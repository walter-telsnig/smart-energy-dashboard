from sqlalchemy import Column, TIMESTAMP, Float
from infra.database import Base

class Market(Base):
    __tablename__ = "market"

    datetime = Column(TIMESTAMP, primary_key=True)
    price_eur_mwh = Column(Float, primary_key=False)