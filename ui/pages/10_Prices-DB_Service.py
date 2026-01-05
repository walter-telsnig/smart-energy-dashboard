import os
import streamlit as st
import requests
import pandas as pd
import pytz
from datetime import datetime, time, timedelta, date

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

from utils.theme import apply_global_style, sidebar_nav

st.set_page_config(layout="wide", page_title="Household Prices DB Service • Smart Energy Dashboard", page_icon="☀️")
apply_global_style()

sidebar_nav(active="🗄️  Prices DB • Service") 

if "token" not in st.session_state or not st.session_state["token"]:
    st.switch_page("pages/00_Login.py")

if "token" not in st.session_state or st.session_state["token"] is None:
    st.warning("Please log in to access this page.")
    st.stop()

st.title("💶 Electricity Prices (EPEX AT) Service - DB Version")

if "price_eur_mwh" not in st.session_state:
    st.session_state.price_eur_mwh = 0.0

option = st.selectbox("15 Minute/Hourly", ("15 Minute", "Hourly"))
st.write("You selected:", option)

if option == "15 Minute":
    path = f"{API_BASE_URL}/api/dataManagment/price_minute-db"
elif option == "Hourly":
    path = f"{API_BASE_URL}/api/dataManagment/price-db"

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
    response = requests.get(path, params={"date_value": date.isoformat()})
    return response


date_value = st.date_input("Date:", value=datetime(2025, 1, 1))
if option == "15 Minute":
    time_value = st.time_input("Time:", value=time(0, 0), step=timedelta(minutes=15))
elif option == "Hourly":
    time_value = st.time_input("Time:", value=time(0, 0), step=timedelta(hours=1))

if isinstance(date_value, date):
    timestamp = datetime(
        date_value.year,
        date_value.month,
        date_value.day,
        time_value.hour,
        time_value.minute,
        time_value.second,
        tzinfo=pytz.UTC,
    )
else:
    raise ValueError("No Date selected")

if button_find:
    result = findData(timestamp)
    if result.status_code == 200:
        if len(result.json()) > 0:
            df = pd.DataFrame(result.json(), columns=["datetime", "price_eur_mwh"])
            df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
            st.session_state.price_eur_mwh_value = df["price_eur_mwh"][0]

price_eur_mwh = st.number_input(
    "€-Price per Megawatt-hour:", key="price_eur_mwh_value", format="%0.5f"
)
if button_add:
    result = findData(timestamp)
    if result.status_code == 200:
        if len(result.json()) == 0:
            response = requests.post(
                path,
                params={
                    "datetime": timestamp.isoformat(),
                    "price_eur_mwh": str(price_eur_mwh),
                },
            )
            if response.status_code == 200:
                st.toast("Done", icon=":material/thumb_up:")
            else:
                st.toast(
                    "Error: " + str(response.status_code), icon=":material/exclamation:"
                )
        else:
            st.toast("Exists already", icon=":material/exclamation:")
    else:
        st.toast("Error: " + str(result.status_code), icon=":material/exclamation:")
elif button_find:
    if result.status_code == 200:
        if len(result.json()) > 0:
            st.dataframe(df, hide_index=True)
            st.toast("Success", icon=":material/thumb_up:")
        else:
            st.toast("No Data", icon=":material/exclamation:")
    else:
        st.toast("Error: " + str(result.status_code), icon=":material/exclamation:")
elif button_edit:
    result = findData(timestamp)
    if result.status_code == 200:
        if len(result.json()) > 0:
            response = requests.put(
                path,
                params={
                    "datetime": timestamp.isoformat(),
                    "price_eur_mwh": str(price_eur_mwh),
                },
            )

            if response.status_code == 200:
                st.toast("Done", icon=":material/thumb_up:")
            else:
                st.toast(
                    "Error: " + str(response.status_code), icon=":material/exclamation:"
                )
        else:
            st.toast(
                "There is no such data. Please add it", icon=":material/exclamation:"
            )
    else:
        st.toast("Error: " + str(result.status_code), icon=":material/exclamation:")
elif button_delete:
    result = findData(timestamp)
    if result.status_code == 200:
        if len(result.json()) > 0:
            response = requests.delete(
                path, params={"date_value": timestamp.isoformat()}
            )

            if response.status_code == 200:
                st.toast("Done", icon=":material/thumb_up:")
            else:
                st.toast(
                    "Error: " + str(result.status_code), icon=":material/exclamation:"
                )
        else:
            st.toast("There is no such data.", icon=":material/exclamation:")
    else:
        st.toast("Error: " + str(result.status_code), icon=":material/exclamation:")
