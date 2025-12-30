import pytz
import numpy as np
from fastapi.testclient import TestClient
from app.main import create_app
from infra.models import Consumption as Consumption
from datetime import datetime, timedelta

client = TestClient(create_app())
start = datetime(2025,1,1)
end = start + timedelta(days=7)
path = "/api/dataManagment/consumption-db"
date = datetime(2028, 12, 31, 0, 0, 0, tzinfo=pytz.UTC)

def test_consumption_db_add():
    resp = client.post(
        path,
        params={
            "datetime": date,
            "consumption_kwh": 0.0
        }
    )
    assert resp.status_code == 200

def test_consumption_db_get():
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

def test_consumption_db_edit():
    resp = client.put(
        path,
        params={
            "datetime": date,
            "consumption_kwh": np.random.random()
        }
    )
    assert resp.status_code == 200

def test_consumption_db_delete():
    resp = client.delete(
            path,
            params={
                "date_value": date
            }
        )
    assert resp.status_code == 200

def test_consumption_db_get_list():
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


def test_consumption_db_get_error():
    resp = client.get(
        path,
    )

    assert resp.status_code != 200    

def test_consumption_db_get_error_list():
    resp = client.get(
        path + "/list",
    )

    assert resp.status_code != 200
