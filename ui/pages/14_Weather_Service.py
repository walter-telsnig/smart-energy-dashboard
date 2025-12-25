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
st.title(":cloud: Weather Service - DB Version")

path = f"{API_BASE_URL}/api/dataManagment/weather-db"

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
time = st.time_input("Time:", value="00:00", step=timedelta(hours=1))

timestamp = datetime(date.year, date.month, date.day, time.hour, time.minute, time.second, tzinfo=pytz.UTC)

temp_c_value = 0.0
cloud_cover_pct_value = 0.0

if button_find:
    result = findData(timestamp)
    if result.status_code == 200:
        if len(result.json()) > 0:
            df = pd.DataFrame(result.json(), columns=["datetime", "temp_c", "cloud_cover_pct"])
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
            temp_c_value = df["temp_c"][0]
            cloud_cover_pct_value = df["cloud_cover_pct"][0]

temp_c = st.number_input("Temperature Celsius:", value=temp_c_value, format="%0.2f")
cloud_cover_pct = st.number_input("Cloud Cover in %:", value=cloud_cover_pct_value, format="%0.2f")

if button_add:
    if cloud_cover_pct > 100:
        st.write("Please take a number equal or less than 100")
    else:
        result = findData(timestamp)
        if result.status_code == 200:
            if len(result.json()) == 0:
                response = requests.post(
                    path+"/add",
                    params={
                        "datetime": timestamp,
                        "temp_c": temp_c,
                        "cloud_cover_pct": cloud_cover_pct
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
    if cloud_cover_pct > 100:
        st.write("Please take a number equal or less than 100")
    else:
        result = findData(timestamp)
        if result.status_code == 200:
            if len(result.json())>0:
                response = requests.put(
                    path,
                    params={
                        "datetime": timestamp,
                        "temp_c": temp_c,
                        "cloud_cover_pct": cloud_cover_pct
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