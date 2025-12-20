import os
import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(layout="wide")
st.title("🏠 Household Consumption - Database Version")

now = datetime.now()

left, right = st.columns(2)
with left:
    start = st.date_input("Start", value=datetime(now.year, 1, 1))
with right:
    end = st.date_input("End", value=datetime(now.year, 1,1)+pd.Timedelta(days=7))

start_ts = pd.Timestamp(start, tz="UTC")
end_ts = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)

response = requests.get(
    f"{API_BASE_URL}/api/dataManagment/consumption-db",
    params={
        "start": start_ts,
        "end": end_ts
    }
)

#--Check Status--
#st.write("Status:", response.status_code)
#st.write("Raw response:", response.text)

df = pd.DataFrame(response.json(), columns=["datetime", "consumption_kwh"])
df["datetime"] = pd.to_datetime(df["datetime"])

chart, stats, preview = st.tabs(["Charts", "Stats", "Preview"])
with chart:
    st.line_chart(df.set_index("datetime")["consumption_kwh"])
