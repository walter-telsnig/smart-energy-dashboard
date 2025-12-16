#consumption.py
#TODO: Implement it in main
from pydantic import BaseModel
from datetime import datetime
import psycopg2
import psycopg2.extras

conn = psycopg2.connect(
    dbname="pv-db", user="postgres", password="ppswy2026", host="localhost"
)

cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

class ConsumptionData(BaseModel):
    datetime: datetime
    consumption_kwh: float

#TODO: create functions for create, get, update and delete
def create_data(data: ConsumptionData):
    cursor.execute(
        "INSERT INTO consumption (datetime, consumption_kwh) VALUES (%s,%s,%s,%s)",
        (data.datetime, data.consumption_kwh)
    )
    conn.commit()
    return{"status": "success"}