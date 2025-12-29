import pytz
import numpy as np
from fastapi.testclient import TestClient
from app.main import create_app
from infra.models import Consumption_Minute as Consumption_Minute
from datetime import datetime, timedelta

client = TestClient(create_app())
start = datetime(2025,1,1)
end = start + timedelta(days=7)
path = "/api/dataManagment/consumption_minute-db"
date = datetime(2028, 12, 31, 0, 0, 0, tzinfo=pytz.UTC)

def test_consumption_minute_db_add():
    resp = client.post(
        path,
        params={
            "datetime": date,
            "consumption_kwh": 0.0,
            "household_general_kwh": 0.0,
            "heat_pump_kwh": 0.0,
            "ev_load_kwh": 0.0,
            "household_base_kwh": 0.0,
            "total_consumption_kwh": 0.0,
            "battery_soc_kwh": 0.0,
            "battery_charging_kwh": 0.0,
            "battery_discharging_kwh": 0.0,
            "grid_export_kwh": 0.0,
            "grid_import_kwh": 0.0
        }
    )
    assert resp.status_code == 200

def test_consumption_minute_db_get():
    resp = client.get(
        path,
        params={
            "date_value": date
        },
    )
    assert resp.status_code == 200

    data = resp.json()
    assert len(data) == 1
    assert isinstance(data, list)

def test_consumption_minute_db_edit():
    resp = client.put(
        path,
        params={
            "datetime": date,
            "consumption_kwh": np.random.random(),
            "household_general_kwh": np.random.random(),
            "heat_pump_kwh": np.random.random(),
            "ev_load_kwh": np.random.random(),
            "household_base_kwh": np.random.random(),
            "total_consumption_kwh": np.random.random(),
            "battery_soc_kwh": np.random.random(),
            "battery_charging_kwh": np.random.random(),
            "battery_discharging_kwh": np.random.random(),
            "grid_export_kwh": np.random.random(),
            "grid_import_kwh": np.random.random()
        }
    )
    assert resp.status_code == 200

def test_consumption_minute_db_delete():
    resp = client.delete(
            path,
            params={
                "date_value": date
            }
        )
    assert resp.status_code == 200

def test_consumption_minute_db_get_list():
    resp = client.get(
        path + "/list",
        params={
            "start": start,
            "end": end
        },
    )
    assert resp.status_code == 200

    data = resp.json()
    assert isinstance(data, list)

def test_consumption_minute_db_get_error():
    resp = client.get(
        path,
    )

    assert resp.status_code != 200

def test_consumption_minute_db_get_error_list():
    resp = client.get(
        path + "/list",
    )

    assert resp.status_code != 200
