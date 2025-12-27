#consumption.py

from pydantic import BaseModel
from datetime import datetime
import psycopg2
import psycopg2.extras
from fastapi import APIRouter

router = APIRouter(prefix="/consumption_minute-db" ,tags=["consumption_minute"])

conn = psycopg2.connect(
    dbname="pv-db", user="postgres", password="ppswy2026", host="localhost"
)

cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

class ConsumptionMinuteData(BaseModel):
    datetime: datetime
    consumption_kwh: float
    household_general_kwh: float
    heat_pump_kwh: float
    ev_load_kwh: float
    household_base_kwh: float
    total_consumption_kwh: float
    battery_soc_kwh: float
    battery_charging_kwh: float
    battery_discharging_kwh: float
    grid_export_kwh: float
    grid_import_kwh: float

#TODO: create functions for create, get, update and delete
@router.post("")
def create_data(datetime: datetime,
    consumption_kwh: float,
    household_general_kwh: float,
    heat_pump_kwh: float,
    ev_load_kwh: float,
    household_base_kwh: float,
    total_consumption_kwh: float,
    battery_soc_kwh: float,
    battery_charging_kwh: float,
    battery_discharging_kwh: float,
    grid_export_kwh: float,
    grid_import_kwh: float):
    cursor.execute(
        "INSERT INTO consumption_minute (datetime, consumption_kwh, household_general_kwh, heat_pump_kwh, ev_load_kwh, household_base_kwh, total_consumption_kwh, battery_soc_kwh, battery_charging_kwh, battery_discharging_kwh, grid_export_kwh, grid_import_kwh) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (datetime, 
        consumption_kwh,
        household_general_kwh,
        heat_pump_kwh,
        ev_load_kwh,
        household_base_kwh,
        total_consumption_kwh,
        battery_soc_kwh,
        battery_charging_kwh,
        battery_discharging_kwh,
        grid_export_kwh,
        grid_import_kwh)
    )
    conn.commit()
    return{"status": "success"}

@router.put("")
def update_data(datetime: datetime,
    consumption_kwh: float,
    household_general_kwh: float,
    heat_pump_kwh: float,
    ev_load_kwh: float,
    household_base_kwh: float,
    total_consumption_kwh: float,
    battery_soc_kwh: float,
    battery_charging_kwh: float,
    battery_discharging_kwh: float,
    grid_export_kwh: float,
    grid_import_kwh: float):
    cursor.execute(
        "UPDATE consumption_minute SET consumption_kwh=%s, household_general_kwh=%s, heat_pump_kwh=%s, ev_load_kwh=%s, household_base_kwh=%s, total_consumption_kwh=%s, battery_soc_kwh=%s, battery_charging_kwh=%s, battery_discharging_kwh=%s, grid_export_kwh=%s, grid_import_kwh=%s "
        "WHERE datetime = %s",
        (consumption_kwh, household_general_kwh, heat_pump_kwh, ev_load_kwh, household_base_kwh, total_consumption_kwh, battery_soc_kwh, battery_charging_kwh, battery_discharging_kwh, grid_export_kwh, grid_import_kwh, datetime)
    )
    conn.commit()
    return{"status": "success"}

@router.get("/list")
def get_data(start: datetime, end: datetime):
    cursor.execute(
        "SELECT datetime, consumption_kwh, household_general_kwh, heat_pump_kwh, ev_load_kwh, household_base_kwh, total_consumption_kwh, battery_soc_kwh, battery_charging_kwh, battery_discharging_kwh, grid_export_kwh, grid_import_kwh FROM consumption_minute "
        "WHERE datetime >= %s AND datetime <= %s ORDER BY datetime",
        (start, end)
    )
    rows = cursor.fetchall()
    return rows

@router.get("")
def get_element(date_value: datetime):
    cursor.execute(
        "SELECT datetime, consumption_kwh, household_general_kwh, heat_pump_kwh, ev_load_kwh, household_base_kwh, total_consumption_kwh, battery_soc_kwh, battery_charging_kwh, battery_discharging_kwh, grid_export_kwh, grid_import_kwh FROM consumption_minute "
        "WHERE datetime = %s",
        (date_value,)
    )
    rows = cursor.fetchall()
    return rows

@router.delete("")
def delete_element(date_value: datetime):
    cursor.execute(
        "DELETE FROM consumption_minute "
        "WHERE datetime = %s",
        (date_value,)
    )
    conn.commit()
    return{"status": "success"}