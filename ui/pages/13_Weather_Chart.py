import os
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, date
from typing import cast

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(layout="wide")

if "token" not in st.session_state or st.session_state["token"] is None:
    st.warning("Please log in to access this page.")
    st.stop()
st.title(":cloud: Weather Chart - DB Version")

path = f"{API_BASE_URL}/api/dataManagment/weather-db"

now = datetime.now()

left, right = st.columns(2)
with left:
    start = cast(date, st.date_input("Start", value=datetime(now.year, 1, 1)))
with right:
    end = cast(date, st.date_input("End", value=datetime(now.year, 1,1)+pd.Timedelta(days=7)))

start_ts = pd.Timestamp(start, tz="UTC")
end_ts = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)

response = requests.get(
    path+"/list",
    params={
        "start": start_ts.isoformat(),
        "end": end_ts.isoformat()
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
