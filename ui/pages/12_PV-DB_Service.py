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
st.title("☀️ PV Production Service - DB Version")

option = st.selectbox("15 Minute/Hourly", ("15 Minute", "Hourly"))
st.write("You selected:", option)

if option == "15 Minute":
    path = f"{API_BASE_URL}/api/dataManagment/pv_minute-db"
elif option == "Hourly":
    path = f"{API_BASE_URL}/api/dataManagment/pv-db"

col1, col2, col3 = st.columns(3)
with col1:
    button_add = st.button("Add Data")
with col2:
    button_find = st.button("Find Data")
with col3:
    button_edit = st.button("Edit Data")

def findData(date: datetime):
    response = requests.get(
        path,
        params={
            "date_value": date
        }
    )
    return response  

date = st.date_input("Date:")
if(option == "15 Minute"):
    time = st.time_input("Time:", value="00:00", step=timedelta(minutes=15))
elif(option == "Hourly"):
    time = st.time_input("Time:", value="00:00", step=timedelta(hours=1))

timestamp = datetime(date.year, date.month, date.day, time.hour, time.minute, time.second, tzinfo=pytz.UTC)

production_kw_value = 0.0

if button_find:
    result = findData(timestamp)
    if result.status_code == 200:
        if len(result.json()) > 0:
            df = pd.DataFrame(result.json(), columns=["datetime", "production_kw"])
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
            production_kw_value = df["production_kw"][0]

production_kw = st.number_input("Production Kilowatt:", value=production_kw_value, format="%0.5f")

if button_add:
    result = findData(timestamp)
    if result.status_code == 200:
        if len(result.json()) == 0:
            response = requests.post(
                path+"/add",
                params={
                    "datetime": timestamp,
                    "production_kw": production_kw
                }
            )
            if response.status_code == 200:
                st.write("Done")
            else:
                st.write("Error: " + response.status_code)
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
        if len(result.json())>0:
            response = requests.put(
                path,
                params={
                    "datetime": timestamp,
                    "production_kw": production_kw
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