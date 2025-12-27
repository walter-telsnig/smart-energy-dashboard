import os
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(layout="wide")

if "token" not in st.session_state or st.session_state["token"] is None:
    st.warning("Please log in to access this page.")
    st.stop()
st.title("☀️ PV Production Chart - DB Version")

option = st.selectbox("15 Minute/Hourly", ("15 Minute", "Hourly"))
st.write("You selected:", option)

if option == "15 Minute":
    path = f"{API_BASE_URL}/api/dataManagment/pv_minute-db"
elif option == "Hourly":
    path = f"{API_BASE_URL}/api/dataManagment/pv-db"

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

#--Check Status--
#st.write("Status:", response.status_code)
#st.write("Raw response:", response.text)

if response.status_code == 200:
    df = pd.DataFrame(response.json(), columns=["datetime", "production_kw"])
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

    chart, stats, preview = st.tabs(["Charts", "Stats", "Preview"])
    with chart:
        st.line_chart(df.set_index("datetime")["production_kw"])
    with stats:
        st.dataframe(df["production_kw"].describe())
    with preview:
        st.write("Number of Results: " + str(len(df.index)))
        if(preview_amount<=len(df.index)):
            st.dataframe(df.head(preview_amount))
        else:
            st.dataframe(df.head(len(df.index)))
else: 
        st.write("No Data")