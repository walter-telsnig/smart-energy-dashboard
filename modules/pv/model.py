# SQLAlchemy persistence model for PV series
from datetime import datetime
from sqlalchemy import DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from infra.db import Base

class PV(Base):
    __tablename__ = "pv"

    # Use timestamp as primary key (hourly timestamps are unique in data files)
    datetime: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    production_kw: Mapped[float] = mapped_column(Float, nullable=False)
