import os
import streamlit as st
import requests
import pandas as pd
import pytz
from datetime import datetime, time, timedelta

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(layout="wide")

if "token" not in st.session_state or st.session_state["token"] is None:
    st.warning("Please log in to access this page.")
    st.stop()
st.title("🏠 Household Consumption Service - Database Version")

option = st.selectbox("15 Minute/Hourly", ("15 Minute", "Hourly"))
st.write("You selected:", option)

if option == "15 Minute":
    path = f"{API_BASE_URL}/api/dataManagment/consumption_minute-db"
elif option == "Hourly":
    path = f"{API_BASE_URL}/api/dataManagment/consumption-db"

col1, col2, col3, col4 = st.columns(4)
with col1:
    button_add = st.button("Add Data")
with col2:
    button_find = st.button("Find Data")
with col3:
    button_edit = st.button("Edit Data")
with col4:
    button_delete = st.button("Delete Data")

def findData(date: datetime):
    response = requests.get(
        path,
        params={
            "date_value": date.isoformat()
        }
    )
    return response

date_value = st.date_input("Date:")
if(option == "15 Minute"):
    time_value = st.time_input("Time:", value=time(0,0), step=timedelta(minutes=15))
elif(option == "Hourly"):
    time_value = st.time_input("Time:", value=time(0,0), step=timedelta(hours=1))

timestamp = datetime(date_value.year, date_value.month, date_value.day, time_value.hour, time_value.minute, time_value.second, tzinfo=pytz.UTC)

result = None
consumption_kwh_value = 0.0
household_general_kwh_value = 0.0
heat_pump_kwh_value = 0.0
ev_load_kwh_value = 0.0
household_base_kwh_value = 0.0
total_consumption_kwh_value = 0.0
battery_soc_kwh_value = 0.0
battery_charging_kwh_value = 0.0
battery_discharging_kwh_value = 0.0
grid_export_kwh_value = 0.0
grid_import_kwh_value = 0.0

if button_find:
    result = findData(timestamp)
    if result.status_code == 200:
        if len(result.json()) > 0:
            if(option == "15 Minute"):
                df = pd.DataFrame(result.json(), columns=["datetime", "consumption_kwh", "household_general_kwh", "heat_pump_kwh", "ev_load_kwh", "household_base_kwh", "total_consumption_kwh", "battery_soc_kwh", "battery_charging_kwh", "battery_discharging_kwh", "grid_export_kwh", "grid_import_kwh"])
                df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

                household_general_kwh_value = df["household_general_kwh"][0]
                heat_pump_kwh_value = df["heat_pump_kwh"][0]
                ev_load_kwh_value = df["ev_load_kwh"][0]
                household_base_kwh_value = df["household_base_kwh"][0]
                total_consumption_kwh_value = df["total_consumption_kwh"][0]
                battery_soc_kwh_value = df["battery_soc_kwh"][0]
                battery_charging_kwh_value = df["battery_charging_kwh"][0]
                battery_discharging_kwh_value = df["battery_discharging_kwh"][0]
                grid_export_kwh_value = df["grid_export_kwh"][0]
                grid_import_kwh_value = df["grid_import_kwh"][0]
            elif(option == "Hourly"):
                df = pd.DataFrame(result.json(), columns=["datetime", "consumption_kwh"])
                df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

            consumption_kwh_value = df["consumption_kwh"][0]

if(option == "15 Minute"):
    household_general_kwh = st.number_input("Household General Kilowatt per Hour:", value=household_general_kwh_value, format="%0.5f")
    heat_pump_kwh = st.number_input("Heatpump Kilowatt per Hour:", value=heat_pump_kwh_value, format="%0.5f")
    ev_load_kwh = st.number_input("EV Load Kilowatt per Hour:", value=ev_load_kwh_value, format="%0.5f")
    household_base_kwh = st.number_input("Household Base Kilowatt per Hour:", value=household_base_kwh_value, format="%0.5f")
    total_consumption_kwh = st.number_input("Total Consumption Kilowatt per Hour:", value=total_consumption_kwh_value, format="%0.5f")
    battery_soc_kwh = st.number_input("Battery State of Charge Kilowatt per Hour:", value=battery_soc_kwh_value, format="%0.5f")
    battery_charging_kwh = st.number_input("Battery Charging Kilowatt per Hour:", value=battery_charging_kwh_value, format="%0.5f")
    battery_discharging_kwh = st.number_input("Battery Discharging Kilowatt per Hour:", value=battery_discharging_kwh_value, format="%0.5f")
    grid_export_kwh = st.number_input("Grid Export Kilowatt per Hour:", value=grid_export_kwh_value, format="%0.5f")
    grid_import_kwh = st.number_input("Grid Import Kilowatt per Hour:", value=grid_import_kwh_value, format="%0.5f")

consumption_kwh = st.number_input("Consumption Kilowatt per Hour:", value=consumption_kwh_value, format="%0.5f")

if button_add:
    result = findData(timestamp)
    if result.status_code == 200:
        if len(result.json()) == 0:
            if(option == "15 Minute"):
                response = requests.post(
                    path,
                    params={
                        "datetime": timestamp.isoformat(),
                        "consumption_kwh": str(consumption_kwh),
                        "household_general_kwh": str(household_general_kwh),
                        "heat_pump_kwh": str(heat_pump_kwh),
                        "ev_load_kwh": str(ev_load_kwh),
                        "household_base_kwh": str(household_base_kwh),
                        "total_consumption_kwh": str(total_consumption_kwh),
                        "battery_soc_kwh": str(battery_soc_kwh),
                        "battery_charging_kwh": str(battery_charging_kwh),
                        "battery_discharging_kwh": str(battery_discharging_kwh),
                        "grid_export_kwh": str(grid_export_kwh),
                        "grid_import_kwh": str(grid_import_kwh)
                    }
                )
            elif(option == "Hourly"):
                response = requests.post(
                    path,
                    params={
                        "datetime": timestamp.isoformat(),
                        "consumption_kwh": str(consumption_kwh)
                    }
                )

            if response.status_code == 200:
                st.write("Done")
            else:
                st.write("Error: " + str(response.status_code))
        else:
            st.write("Exists already")
    else:
        st.write("Error: " + str(result.status_code))
elif button_find:
    if result.status_code == 200:
        if len(result.json()) > 0:
            st.dataframe(df, hide_index=True)
        else:
            st.write("No Data")
    else:
        st.write("Error: " + str(result.status_code))
elif button_edit:
    result = findData(timestamp)
    if result.status_code == 200:
        if len(result.json()) > 0:
            if option == "15 Minute":
                response = requests.put(
                    path,
                    params={
                        "datetime": timestamp.isoformat(),
                        "consumption_kwh": str(consumption_kwh),
                        "household_general_kwh": str(household_general_kwh),
                        "heat_pump_kwh": str(heat_pump_kwh),
                        "ev_load_kwh": str(ev_load_kwh),
                        "household_base_kwh": str(household_base_kwh),
                        "total_consumption_kwh": str(total_consumption_kwh),
                        "battery_soc_kwh": str(battery_soc_kwh),
                        "battery_charging_kwh": str(battery_charging_kwh),
                        "battery_discharging_kwh": str(battery_discharging_kwh),
                        "grid_export_kwh": str(grid_export_kwh),
                        "grid_import_kwh": str(grid_import_kwh)
                    }
                )
            elif option == "Hourly":
                response = requests.put(
                    path,
                    params={
                        "datetime": timestamp.isoformat(),
                        "consumption_kwh": str(consumption_kwh)
                    }
                )

            if response.status_code == 200:
                st.write("Done")
            else:
                st.write("Error: " + str(response.status_code))
        else:
            st.write("There is no such data. Please add it")
    else:
        st.write("Error: " + str(result.status_code))
elif button_delete:
    result = findData(timestamp)
    if result.status_code == 200:
        if len(result.json()) > 0:
            response = requests.delete(
                path,
                params={
                    "date_value": timestamp.isoformat()
                }
            )

            if response.status_code == 200:
                st.write("Done")
            else:
                st.write("Error: " + str(result.status_code))
        else:
            st.write("There is no such data.")
    else:
        st.write("Error: " + str(result.status_code))