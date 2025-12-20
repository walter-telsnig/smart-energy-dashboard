#consumption.py
#TODO: Implement it in main

from pydantic import BaseModel
from datetime import datetime
from pandas import DataFrame
import psycopg2
import psycopg2.extras
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/consumption-db" ,tags=["consumption"])

conn = psycopg2.connect(
    dbname="pv-db", user="postgres", password="ppswy2026", host="localhost"
)

cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

class ConsumptionData(BaseModel):
    datetime: datetime
    consumption_kwh: float

#TODO: create functions for create, get, update and delete
@router.post("/add")
def create_data(data: ConsumptionData):
    cursor.execute(
        "INSERT INTO consumption (datetime, consumption_kwh) VALUES (%s,%s,%s,%s)",
        (data.datetime, data.consumption_kwh)
    )
    conn.commit()
    return{"status": "success"}

@router.get("")
def get_data(start: datetime, end: datetime):
    cursor.execute(
        "SELECT datetime, consumption_kwh FROM consumption "
        "WHERE datetime >= %s AND datetime <= %s ORDER BY datetime",
        (start, end)
    )
    rows = cursor.fetchall()
    return rows