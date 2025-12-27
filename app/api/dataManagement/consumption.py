#consumption.py

from pydantic import BaseModel
from datetime import datetime
import psycopg2
import psycopg2.extras
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/consumption-db" ,tags=["consumption"])

conn = psycopg2.connect(
    dbname="pv-db", user="postgres", password="ppswy2026", host="localhost"
)

try:
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
except psycopg2.OperationalError:
    pass

class ConsumptionData(BaseModel):
    datetime: datetime
    consumption_kwh: float

#TODO: create functions for create, get, update and delete
@router.post("")
def create_data(datetime: datetime, consumption_kwh: float):
    cursor.execute(
        "INSERT INTO consumption (datetime, consumption_kwh) VALUES (%s,%s)",
        (datetime, consumption_kwh)
    )
    conn.commit()
    return{"status": "success"}

@router.put("")
def update_data(datetime: datetime, consumption_kwh: float):
    cursor.execute(
        "UPDATE consumption SET consumption_kwh=%s "
        "WHERE datetime = %s",
        (consumption_kwh, datetime)
    )
    conn.commit()
    return{"status": "success"}

@router.get("/list")
def get_data(start: datetime, end: datetime):
    cursor.execute(
        "SELECT datetime, consumption_kwh FROM consumption "
        "WHERE datetime >= %s AND datetime <= %s ORDER BY datetime",
        (start, end)
    )
    rows = cursor.fetchall()
    return rows

@router.get("")
def get_element(date_value: datetime):
    cursor.execute(
        "SELECT datetime, consumption_kwh FROM consumption "
        "WHERE datetime = %s",
        (date_value,)
    )
    rows = cursor.fetchall()
    return rows

@router.delete("")
def delete_element(date_value: datetime):
    cursor.execute(
        "SELECT datetime, consumption_kwh FROM consumption "
        "WHERE datetime = %s",
        (date_value,)
    )
    rows = cursor.fetchall()
    return rows