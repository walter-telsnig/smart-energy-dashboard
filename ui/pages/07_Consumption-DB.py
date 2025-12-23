import os
import streamlit as st
import requests
import pandas as pd
import pytz
from datetime import datetime, timedelta

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(layout="wide")

if "token" not in st.session_state or st.session_state["token"] is None:
    st.warning("Please log in to access this page.")
    st.stop()
st.title("🏠 Household Consumption - Database Version")

option = st.selectbox("15 Minute/Hourly", ("15 Minute", "Hourly"))
st.write("You selected:", option)

if option == "15 Minute":
    path = f"{API_BASE_URL}/api/dataManagment/consumption_minute-db"
elif option == "Hourly":
    path = f"{API_BASE_URL}/api/dataManagment/consumption-db"

def existData(date: datetime):
    response = requests.get(
        path,
        params={
            "date_value": date
        }
    )
    if response.status_code == 200:
        if(len(response.json()) > 0):
            return True
        else:
            return False
    else:
        return None

#TODO: Find a solution for minutes and finish it
with st.expander("Add Data"):
    date = st.date_input("Date:")
    if(option == "15 Minute"):
        time = st.time_input("Time:", value="00:00", step=timedelta(minutes=15))
    elif(option == "Hourly"):
        time = st.time_input("Time:", value="00:00", step=timedelta(hours=1))
    consumption_kwh = st.number_input("Kilowatt per Hour:")
    if st.button("Confirm"):
        if(option == "15 Minute"):
            st.write("In Work")
            #response = requests.post(
             #   f"{API_BASE_URL}/api/dataManagment/consumption_minute-db",
             #   params={

              #  }
            #)
        elif(option == "Hourly"):
            timestamp = datetime(date.year, date.month, date.day, time.hour, time.minute, time.second, tzinfo=pytz.UTC)
            exists = existData(timestamp)
            if exists is None:
                st.write("Error")
            elif not exists:
                response = requests.post(
                    path+"/add",
                    params={
                        "datetime": timestamp,
                        "consumption_kwh": consumption_kwh
                    }
                )
                if response.status_code == 200:
                    st.write("Done")
                else:
                    st.write("Error: " + response.status_code)
            else:
                st.write("Exists already")


now = datetime.now()

left, right = st.columns(2)
with left:
    start = st.date_input("Start", value=datetime(now.year, 1, 1))
with right:
    end = st.date_input("End", value=datetime(now.year, 1,1)+pd.Timedelta(days=7))

start_ts = pd.Timestamp(start, tz="UTC")
end_ts = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)

preview_amount = st.number_input("preview_amount",value=48)

response = requests.get(
        path+"/list",
        params={
            "start": start_ts,
            "end": end_ts
        }
    )

if response.status_code == 200:
    if(option == "15 Minute"):
        df = pd.DataFrame(response.json(), columns=["datetime", "consumption_kwh", "household_general_kwh", "heat_pump_kwh", "ev_load_kwh", "household_base_kwh", "total_consumption_kwh", "battery_soc_kwh", "battery_charging_kwh", "battery_discharging_kwh", "grid_export_kwh", "grid_import_kwh"])
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    elif(option == "Hourly"):
        df = pd.DataFrame(response.json(), columns=["datetime", "consumption_kwh"])
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        
    chart, stats, preview = st.tabs(["Charts", "Stats", "Preview"])
    with chart:
        st.line_chart(df.set_index("datetime")["consumption_kwh"])
    with stats:
        st.dataframe(df.iloc[:,1:].describe())
    with preview:
        st.write("Number of Results: " + str(len(df.index)))
        if(preview_amount<=len(df.index)):
            st.dataframe(df.head(preview_amount))
        else:
            st.dataframe(df.head(len(df.index)))
else: 
        st.write("No Data")

#--Check Status--
#st.write("Status:", response.status_code)
#st.write("Raw response:", response.text)