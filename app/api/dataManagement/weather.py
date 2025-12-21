#weather.py

from pydantic import BaseModel
from datetime import datetime
import psycopg2
import psycopg2.extras
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/weather-db" ,tags=["weather"])

conn = psycopg2.connect(
    dbname="pv-db", user="postgres", password="ppswy2026", host="localhost"
)

cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

class WeatherData(BaseModel):
    datetime: datetime
    temp_c: float
    cloud_cover_pct: float

#TODO: create functions for create, get, update and delete
@router.post("/add")
def create_data(data: WeatherData):
    cursor.execute(
        "INSERT INTO weather (datetime, temp_c, cloud_cover_pct) VALUES (%s,%s, %s)",
        (data.datetime, data.temp_c, data.cloud_cover_pct)
    )
    conn.commit()
    return{"status": "success"}

@router.get("")
def get_data(start: datetime, end: datetime):
    cursor.execute(
        "SELECT datetime, temp_c, cloud_cover_pct FROM weather "
        "WHERE datetime >= %s AND datetime <= %s ORDER BY datetime",
        (start, end)
    )
    rows = cursor.fetchall()
    return rows