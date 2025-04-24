import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


API_BASE_URL = "http://localhost:8000/api"

def get_headers():
    if "access_token" not in st.session_state:
        return {}
    return {"Authorization": f"Bearer {st.session_state['access_token']}"}


def get_blood_pressure_data(days=1):
    """Get blood pressure data for the specified number of days"""
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    response = requests.get(
        f"{API_BASE_URL}/blood-pressure/?start_date={start_date}",
        headers=get_headers()
    )

    if response.status_code == 200:
        data = response.json()
        if data:
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
    return pd.DataFrame()

def get_daily_steps_data(days=7):
    """Get daily data for the specified number of days"""
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    response = requests.get(
        f"{API_BASE_URL}/daily-steps/?start_date={start_date}",
        headers=get_headers()
    )

    if response.status_code == 200:
        data = response.json()
        if data:
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
    return pd.DataFrame()

def get_heart_rate_data(days=1):
    """Get heart rate data for the specified number of days"""
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    response = requests.get(
        f"{API_BASE_URL}/heart-rate/?start_date={start_date}",
        headers=get_headers()
    )

    if response.status_code == 200:
        data = response.json()
        if data:
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
    return pd.DataFrame()

def get_sleep_duration_data(days=7):
    """Get sleep duration data for the specified number of days"""
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    response = requests.get(
        f"{API_BASE_URL}/sleep-duration/?start_date={start_date}",
        headers=get_headers()
    )

    if response.status_code == 200:
        data = response.json()
        if data:
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
    return pd.DataFrame()

def get_spo2_data(days=1):
    """Get spo2 data for the specified number of days"""
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    response = requests.get(
        f"{API_BASE_URL}/spo2/?start_date={start_date}",
        headers=get_headers()
    )

    if response.status_code == 200:
        data = response.json()
        if data:
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
    return pd.DataFrame()