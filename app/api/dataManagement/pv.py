#pv.py

from pydantic import BaseModel
from datetime import datetime
import psycopg2
import psycopg2.extras
from fastapi import APIRouter

router = APIRouter(prefix="/pv-db" ,tags=["pv"])

conn = psycopg2.connect(
    dbname="pv-db", user="postgres", password="ppswy2026", host="localhost"
)

cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

class PVData(BaseModel):
    datetime: datetime
    production_kw: float

#TODO: create functions for create, get, update and delete
@router.post("")
def create_data(datetime: datetime, production_kw: float):
    cursor.execute(
        "INSERT INTO pv (datetime, production_kw) VALUES (%s,%s)",
        (datetime, production_kw)
    )
    conn.commit()
    return{"status": "success"}

@router.put("")
def update_data(datetime: datetime, production_kw: float):
    cursor.execute(
        "UPDATE pv SET production_kw=%s "
        "WHERE datetime = %s",
        (production_kw, datetime)
    )
    conn.commit()
    return{"status": "success"}

@router.get("/list")
def get_data(start: datetime, end: datetime):
    cursor.execute(
        "SELECT datetime, production_kw FROM pv "
        "WHERE datetime >= %s AND datetime <= %s ORDER BY datetime",
        (start, end)
    )
    rows = cursor.fetchall()
    return rows

@router.get("")
def get_element(date_value: datetime):
    cursor.execute(
        "SELECT datetime, production_kw FROM pv "
        "WHERE datetime = %s",
        (date_value,)
    )
    rows = cursor.fetchall()
    return rows

@router.delete("")
def delete_element(date_value: datetime):
    cursor.execute(
        "DELETE FROM pv "
        "WHERE datetime = %s",
        (date_value,)
    )
    conn.commit()
    return{"status": "success"}