from datetime import datetime
from sqlalchemy import DateTime, Float
from sqlalchemy.orm import Mapped, mapped_column
from infra.db import Base

class Consumption(Base):
    __tablename__ = "consumption"

    datetime: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    consumption_kwh: Mapped[float] = mapped_column(Float, nullable=False)
