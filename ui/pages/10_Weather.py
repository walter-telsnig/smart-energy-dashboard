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
st.title(":cloud: Weather - DB Version")

path = f"{API_BASE_URL}/api/dataManagment/weather-db"

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

with st.expander("Add Data"):
    date = st.date_input("Date:")
    time = st.time_input("Time:", value="00:00", step=timedelta(hours=1))
    temp_c = st.number_input("Temperature Celsius:")
    cloud_cover_pct = st.number_input("Cloud Cover in %:")
    if st.button("Confirm"):
        timestamp = datetime(date.year, date.month, date.day, time.hour, time.minute, time.second, tzinfo=pytz.UTC)
        exists = existData(timestamp)
        if exists is None:
            st.write("Error")
        elif not exists:
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

now = datetime.now()

left, right = st.columns(2)
with left:
    start = st.date_input("Start", value=datetime(now.year, 1, 1))
with right:
    end = st.date_input("End", value=datetime(now.year, 1,1)+pd.Timedelta(days=7))

start_ts = pd.Timestamp(start, tz="UTC")
end_ts = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)

response = requests.get(
    path+"/list",
    params={
        "start": start_ts,
        "end": end_ts
    }
)

#--Check Status--
#st.write("Status:", response.status_code)
#st.write("Raw response:", response.text)
preview_amount = st.number_input("preview_amount",value=48)

if response.status_code == 200: 
    df = pd.DataFrame(response.json(), columns=["datetime", "temp_c", "cloud_cover_pct"])
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

    chart_temp, stats, preview = st.tabs(["Charts", "Stats", "Preview"])
    with chart_temp:
        st.write("Line Chart - Temperature")
        st.line_chart(df.set_index("datetime")["temp_c"])
        st.write("Line Chart - Cloud Cover in %")
        st.line_chart(df.set_index("datetime")["cloud_cover_pct"])
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
