#market.py

from pydantic import BaseModel
from datetime import datetime
import psycopg2
import psycopg2.extras
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/price-db" ,tags=["price"])

conn = psycopg2.connect(
    dbname="pv-db", user="postgres", password="ppswy2026", host="localhost"
)

cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

class MarketData(BaseModel):
    datetime: datetime
    price_eur_mwh: float

#TODO: create functions for create, get, update and delete
@router.post("/add")
def create_data(datetime: datetime, price_eur_mwh: float):
    cursor.execute(
        "INSERT INTO market (datetime, price_eur_mwh) VALUES (%s,%s)",
        (datetime, price_eur_mwh)
    )
    conn.commit()
    return{"status": "success"}

@router.get("/list")
def get_data(start: datetime, end: datetime):
    cursor.execute(
        "SELECT datetime, price_eur_mwh FROM market "
        "WHERE datetime >= %s AND datetime <= %s ORDER BY datetime",
        (start, end)
    )
    rows = cursor.fetchall()
    return rows

@router.get("")
def get_element(date_value: datetime):
    cursor.execute(
        "SELECT datetime, price_eur_mwh FROM market "
        "WHERE datetime = %s",
        (date_value,)
    )
    rows = cursor.fetchall()
    return rows