import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json

API_BASE_URL = "http://localhost:8000/api"

def get_headers():
    if "access_token" not in st.session_state:
        return {}
    return {"Authorization": f"Bearer {st.session_state['access_token']}"}


def get_blood_pressure_data(days=7) -> pd.DataFrame:
    """Get blood pressure data for the specified number of days"""
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    response = requests.get(
        f"{API_BASE_URL}/blood-pressure/?start_date={start_date}",
        headers=get_headers()
    )

    if response.status_code == 200:
        data = response.json()
        if data:
            df = pd.DataFrame(data['results'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
    return pd.DataFrame()

def get_daily_steps_data(days=7) -> pd.DataFrame:
    """Get daily data for the specified number of days"""
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    response = requests.get(
        f"{API_BASE_URL}/daily-steps/?start_date={start_date}",
        headers=get_headers()
    )

    if response.status_code == 200:
        data = response.json()
        if data:
            df = pd.DataFrame(data['results'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
    return pd.DataFrame()

def get_heart_rate_data(days=1) -> pd.DataFrame:
    """Get heart rate data for the specified number of days"""
    start_date = (datetime.now()  - timedelta(days=days)).strftime('%Y-%m-%d')
    initial_url = f"{API_BASE_URL}/heart-rate/?start_date={start_date}"
    print(f"Requesting initial URL: {initial_url}")

    headers = get_headers()
    all_results = _get_all_paginated_results(initial_url, headers)

    if all_results:
        df = pd.DataFrame(all_results)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        print(f"Total records fetched: {len(df)}")
        print(f"Unique activity levels in final DataFrame:{df['activity_level'].unique()}")
        return df
    else:
        print("No heart rate results fetched or returned empty")
        return pd.DataFrame()
    

def get_sleep_duration_data(days=7) -> pd.DataFrame:
    """Get sleep duration data for the specified number of days"""
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    response = requests.get(
        f"{API_BASE_URL}/sleep-duration/?start_date={start_date}",
        headers=get_headers()
    )

    if response.status_code == 200:
        data = response.json()
        if data:
            df = pd.DataFrame(data['results'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
    return pd.DataFrame()

def get_spo2_data(days=1) -> pd.DataFrame:
    """Get spo2 data for the specified number of days"""
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    response = requests.get(
        f"{API_BASE_URL}/spo2/?start_date={start_date}",
        headers=get_headers()
    )

    if response.status_code == 200:
        data = response.json()
        if data:
            df = pd.DataFrame(data['results'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            return df
    return pd.DataFrame()


def _get_all_paginated_results(url, headers):
    """Helper to fetch all results from a paginated endpoint."""
    results = []
    current_url = url
    while current_url:
        try:
            response = requests.get(current_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            results.extend(data.get('results', []))
            current_url = data.get('next')
        except requests.exceptions.RequestException as e:
            print(f"API request error fetching page {current_url}: {e}")
            break
        except json.JSONDecodeError:
            print(f"Failed to decode JSON from {current_url}")
            break
    return results
    

  
