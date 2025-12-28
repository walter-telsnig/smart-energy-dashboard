from sqlalchemy import Column, TIMESTAMP, Float
from infra.database import Base

class Consumption_Minute(Base):
    __tablename__ = "consumption_minute"

    datetime = Column(TIMESTAMP, primary_key=True)
    consumption_kwh = Column(Float, primary_key=False)
    household_general_kwh = Column(Float, primary_key=False)
    heat_pump_kwh = Column(Float, primary_key=False)
    ev_load_kwh = Column(Float, primary_key=False)
    household_base_kwh = Column(Float, primary_key=False)
    total_consumption_kwh = Column(Float, primary_key=False)
    battery_soc_kwh = Column(Float, primary_key=False)
    battery_charging_kwh = Column(Float, primary_key=False)
    battery_discharging_kwh = Column(Float, primary_key=False)
    grid_export_kwh = Column(Float, primary_key=False)
    grid_import_kwh = Column(Float, primary_key=False)
