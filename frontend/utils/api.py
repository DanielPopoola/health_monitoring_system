import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import logging
import time
from functools import wraps
from typing import Optional, List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s -%(levelname)s -%(messages)s')

API_BASE_URL = "http://localhost:8000/api"


def paginated_dataframe(
        page_size: int = 100,
        max_records: Optional[int] = None,
        max_pages: Optional[int] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
):
    """
    Decorator that transforms a single-page fetching function into a generator that handles pagination
    automatically, with safeguards for memory usage.
  """
    def decorator(fetch_func):
        @wraps(fetch_func)
        def wrapper(*args, **kwargs):
            """
            Wraps a function that fetches a single page of data and transforms it into a generator that handles pagination
            with proper error handling. The wrapped function must accept 'page' and 'page_size' kwargs. It SHOULD
            return the list of results or None/empty list if no data.
            """
            logging.info(f"Beginning paginated fetch with page_size={page_size}")

            current_page = 1
            records_fetched = 0
            pages_fetched = 0

            while True:
                # Handles retries for network/service failures
                retries = 0
                page_data = None 
                while retries <= max_retries:
                    try:
                        # Call the original function to fetch a single page data
                        page_data = fetch_func(page=current_page, page_size=page_size, *args, **kwargs)
                        break
                    except Exception as e:
                        retries += 1
                        logging.warning(f"Fetch error (attempt {retries}/{max_retries}): {e}")
                        if retries > max_retries:
                            raise RuntimeError(
                                f"Failed to fetch page {current_page} after {max_retries} retries"
                                ) from e
                        time.sleep(retry_delay)

                # Circuit breaker : no more data
                if not page_data:
                    logging.info(f"No more page data available after {current_page-1}")
                    break

                # Yield the page data (the list of results)
                yield page_data

                # Update counters
                # Assuming page_data is a list here, adjust it it's dict['results']
                page_size_actual = len(page_data) if isinstance(page_data, list) else 0
                records_fetched += page_size_actual
                pages_fetched += 1

                # Stop if the page fetched less than requested (likely the last page)
                # This is an alternative/addition to 'if not page_data' if fetch_func
                # returns the last partial page instead of None on the *next* call.
                if page_size_actual < page_size:
                    logging.info(f"Fetched last page ({current_page}) with {page_size_actual} records")
                    break

                # Circut breaker: max records limit
                if max_records and records_fetched >= max_records:
                    logging.info(f"Reached max records limit ({max_records})")
                    break

                # Circuit breaker: max pages limit
                if max_pages and pages_fetched >= max_pages:
                    logging.info(f"Reached max pages limit ({max_pages})")
                    break

                current_page += 1

            logging.info(
                f"Pagination complete: {records_fetched} records across {pages_fetched} pages"
            )

        return wrapper
    return decorator
            

def get_headers():
    if "access_token" not in st.session_state:
        return {}
    return {"Authorization": f"Bearer {st.session_state['access_token']}"}

def _fetch_paginated_data(endpoint_url:str, page: int, page_size:int, headers: Dict[str, str], 
                          params: Optional[Dict[str, Any]] = None) -> Optional[List[Dict]]:
    """
    Internal helper to fetch one page from DRF endpoint.
    Returns the list of results or None if no data/error.
    """
    if params is None:
        params = {}
    # Add pagination params
    params['page'] = page
    params['page_size'] = page_size

    try:
        response = requests.get(endpoint_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        results = data['results']

        if not results:
            return None # No more results on this page (or endpoint is empty)
        return results
    except requests.exceptions.RequestException as e:
        logging.error(f"API request error fetching page {page} from {endpoint_url}: {e}")
        raise
    except json.JSONDecodeError:
        logging.error(f"Failed to decode JSON from {endpoint_url} (page {page})")
        raise

@paginated_dataframe(page_size=100)
def _get_heart_rate_pages(*, page: int, page_size: int, headers: Dict, start_date: str):
    """Fetches a single page of heart rate data."""
    url = f"{API_BASE_URL}/heart-rate/"
    params = {'start_date': start_date}
    return _fetch_paginated_data(url, page, page_size, headers, params)

def get_heart_rate_data(days: int = 1) -> pd.DataFrame:
    """Get ALL heart rate data, using the paginated fetcher."""
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    headers = get_headers()
    all_results = []

    # The decorated function returns a generator
    page_generator = _get_heart_rate_pages(headers=headers, start_date=start_date)

    try:
        for page_data in page_generator:
            if page_data:
                all_results.extend(page_data)
    except RuntimeError as e:
        st.error(f"Failed to fetch complete heart rate data: {e}")
        logging.error(f"RuntimeError during heart rate pagination: {e}")
        return pd.DataFrame()
    
    if all_results:
        df = pd.DataFrame(all_results)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        logging.info(f"Total heart rate records processed: {len(df)}")
        if not df.empty and 'activity_level' in df.columns:
            logging.info(f"Unique activity levels in final DataFrame: {df['activity_level'].unique()}")
        return df
    else:
        logging.info("No heart rate results fetched or returned empty.")
        return pd.DataFrame()


@paginated_dataframe(page_size=100)
def _get_daily_steps_pages(*, page: int, page_size: int, headers: Dict, start_date: str):
    """Fetch single page of daily steps data"""
    url = f"{API_BASE_URL}/daily-steps/"
    params = {'start_date': start_date}
    return _fetch_paginated_data(url, page, page_size, headers, params)


def get_daily_steps_data(days=7) -> pd.DataFrame:
    """Get ALL Daily Steps data, using the paginated fetcher."""
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    headers = get_headers()
    all_results = []
    page_generator = _get_daily_steps_pages(headers=headers, start_date=start_date)
    try:
        for page_data in page_generator:
            if page_data:
                all_results.extend(page_data)
    except RuntimeError as e:
        st.error(f"Failed to fetch complete daily steps data: {e}")
        logging.error(f"RuntimeError during daily steps pagination: {e}")
        return pd.DataFrame()
    
    if all_results:
        df = pd.DataFrame(all_results)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        logging.info(f"Total daily steps records processed: {len(df)}")
        return df
    else:
        logging.info("No daily steps results fetched or returned empty")
        return pd.DataFrame()
    

@paginated_dataframe(page_size=100)
def _get_blood_pressure_pages(*, page: int, page_size: int, headers: Dict, start_date: str):
    """Fetches a single page of blood pressure data"""
    url = f"{API_BASE_URL}/blood-pressure/"
    params = {'start_date': start_date}
    return _fetch_paginated_data(url, page, page_size, headers, params)

def get_blood_pressure_data(days):
    """Get ALL Blood pressure data, using the paginated fetcher."""
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    headers = get_headers()
    all_results = []
    page_generator = _get_blood_pressure_pages(headers=headers, start_date=start_date)
    try:
        for page_data in page_generator:
            if page_data:
                all_results.extend(page_data)
    except RuntimeError as e:
        st.error(f"Failed to fetch complete blood pressure data: {e}")
        logging.error(f"RuntimeError during blood pressure pagination: {e}")
        return pd.DataFrame()
    
    if all_results:
        df = pd.DataFrame(all_results)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        logging.info(f"Total blood pressure records processed: {len(df)}")
        return df
    else:
        logging.info("No blood pressure results fetched or returned empty")
        return pd.DataFrame()


@paginated_dataframe(page_size=100)
def _get_sleep_duration_pages(*, page: int, page_size: int, headers: Dict, start_date: str):
    """Fetch single page sleep duration data"""
    url = f"{API_BASE_URL}/sleep-duration/"
    params = {'start_date': start_date}
    return _fetch_paginated_data(url, page, page_size, headers, params)

def get_sleep_duration_data(days: int = 1) -> pd.DataFrame:
    """Get ALL Sleep Duration data, using the paginated fetcher."""
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    headers = get_headers()
    all_results = []
    page_generator = _get_spo2_pages(headers=headers, start_date=start_date)
    try:
        for page_data in page_generator:
            if page_data: all_results.extend(page_data)
    except RuntimeError as e:
        st.error(f"Failed to fetch complete Sleep Duration data: {e}")
        logging.error(f"RuntimeError during Sleep Duration pagination: {e}")
        return pd.DataFrame()

    if all_results:
        df = pd.DataFrame(all_results)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    return pd.DataFrame()

    

@paginated_dataframe(page_size=100)
def _get_spo2_pages(*, page: int, page_size: int, headers: Dict, start_date: str):
    """Fetches a single page of SpO2 data."""
    url = f"{API_BASE_URL}/spo2/"
    params = {'start_date': start_date}
    return _fetch_paginated_data(url, page, page_size, headers, params)

def get_spo2_data(days: int = 1) -> pd.DataFrame:
    """Get ALL SpO2 data, using the paginated fetcher."""
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    headers = get_headers()
    all_results = []
    page_generator = _get_spo2_pages(headers=headers, start_date=start_date)
    try:
        for page_data in page_generator:
            if page_data: all_results.extend(page_data)
    except RuntimeError as e:
        st.error(f"Failed to fetch complete SpO2 data: {e}")
        logging.error(f"RuntimeError during SpO2 pagination: {e}")
        return pd.DataFrame()

    if all_results:
        df = pd.DataFrame(all_results)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    return pd.DataFrame()


