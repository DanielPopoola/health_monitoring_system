import requests
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import logging
import time
from functools import wraps
from typing import Optional, List, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
                    except requests.exceptions.HTTPError as e:
                        status_code = e.response.status_code
                        logging.warning(f"Fetch HTTP error (status {status_code}, attempt {retries+1}/{max_retries+1}) \
                                        on page {current_page}: {e}")
                        if status_code in [401, 403]:
                            st.error(f"Authentication or Permission Error ({status_code}). Please login again or check permissions.")
                            raise RuntimeError(f"Permission denied ({status_code}) accessing {fetch_func.__name__}") from e
                        if status_code == 404:
                            logging.warning(f"Resource not found (404) on page {current_page}. Assuming end of data.")
                            page_data = None # Treat as end of data
                            break # Stop retrying 404

                        retries += 1
                        if retries > max_retries:
                            st.error(f"API Server Error ({status_code}) fetching page {current_page}. Please try again later.")
                            raise RuntimeError(f"Failed to fetch page {current_page} after {max_retries} \
                                               retries due to HTTP {status_code}") from e
                        time.sleep(retry_delay)
                    except Exception as e:
                        retries += 1
                        logging.warning(f"Generic fetch error (attempt {retries}/{max_retries}): {e}")
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
                page_size_actual = len(page_data) if isinstance(page_data, list) else 0
                records_fetched += page_size_actual
                pages_fetched += 1

                # Stop if the page fetched less than requested (likely the last page)
                if page_size_actual < page_size:
                    logging.info(f"Fetched last page ({current_page}) with {page_size_actual} records for {fetch_func.__name__}")
                    break

                # Circut breaker: max records limit
                if max_records and records_fetched >= max_records:
                    logging.info(f"Reached max records limit ({max_records}) for {fetch_func.__name__}")
                    break

                # Circuit breaker: max pages limit
                if max_pages and pages_fetched >= max_pages:
                    logging.info(f"Reached max pages limit ({max_pages}) for {fetch_func.__name__}")
                    break

                current_page += 1

            logging.info(
                f"Pagination complete for {fetch_func.__name__}: {records_fetched} records across {pages_fetched} pages"
            )

        return wrapper
    return decorator
            

def get_headers() -> Dict[str, str]:
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
        logging.debug(f"Fetching page {page} from {endpoint_url} with params: {params}")
        response = requests.get(endpoint_url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        results = data['results']

        if not results:
            logging.debug(f"No results found on page {page} for {endpoint_url}")
            return None # No more results on this page (or endpoint is empty)
        return results
    except requests.exceptions.Timeout:
        logging.error(f"API request timed out fetching page {page} from {endpoint_url}")
    except requests.exceptions.RequestException as e:
        logging.error(f"API request error fetching page {page} from {endpoint_url}: {e}")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from {endpoint_url} (page {page}): {e}. Response text: {response.text[:500]}")
        raise

# --- Heart Rate ---

@paginated_dataframe(page_size=100)
def _get_heart_rate_pages(*, page: int, page_size: int, headers: Dict, start_datetime: str, user_id: Optional[int] = None):
    """Fetches a single page of heart rate data."""
    url = f"{API_BASE_URL}/heart-rate/"
    params = {'start_date': start_datetime}
    if user_id is not None:
        params['user_id'] = user_id
    logging.debug(f"Fetching heart rate page {page} with params: {params}")
    return _fetch_paginated_data(url, page, page_size, headers, params)

def get_heart_rate_data(days: int = 1, hours: int = 0, user_id: Optional[int] = None) -> pd.DataFrame:
    """
    Fetch heart rate data starting from now minus the specified days and hours.
    You can use days=0 and hours=1 to fetch just the last hour of data.
    """
    start_date_obj = datetime.now() - timedelta(days=days, hours=hours)
    start_datetime_iso = start_date_obj.strftime('%Y-%m-%dT%H:%M:%S')
    headers = get_headers()
    if not headers: return pd.DataFrame()

    all_results = []
    page_generator = _get_heart_rate_pages(headers=headers, start_datetime=start_datetime_iso, user_id=user_id)
    try:
        for page_data in page_generator:
            if page_data: all_results.extend(page_data)
    except (RuntimeError, requests.exceptions.RequestException) as e:
        # Catch errors raised by the generator/fetcher if retries failed
        st.error(f"Failed to fetch heart rate data: {e}")
        logging.error(f"Error during heart rate pagination: {e}")
        return pd.DataFrame()
    
    if all_results:
        df = pd.DataFrame(all_results)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601', errors='coerce')
        logging.info(f"Total heart rate records processed for user {user_id or 'self'} : {len(df)}")
        if not df.empty and 'activity_level' in df.columns:
            logging.info(f"Unique activity levels in final DataFrame: {df['activity_level'].unique()}")
        return df.sort_values(by='timestamp').reset_index(drop=True)
    else:
        logging.info("No heart rate results fetched or returned empty.")
        return pd.DataFrame()

# --- Daily Steps ---

@paginated_dataframe(page_size=100)
def _get_daily_steps_pages(*, page: int, page_size: int, headers: Dict, start_date: str, user_id: Optional[int] = None):
    """Fetch single page of daily steps data"""
    url = f"{API_BASE_URL}/daily-steps/"
    params = {'start_date': start_date}
    if user_id is not None:
        params['user_id'] = user_id
    logging.debug(f"Fetching daily steps page {page} with params: {params}")
    return _fetch_paginated_data(url, page, page_size, headers, params)


def get_daily_steps_data(days: int = 7, user_id: Optional[int] = None) -> pd.DataFrame:
    """Get ALL Daily Steps data, using the paginated fetcher."""
    start_date_obj = datetime.now() - timedelta(days=days)
    start_date = start_date_obj.strftime('%Y-%m-%d')
    headers = get_headers()
    if not headers: return pd.DataFrame()

    all_results = []
    page_generator = _get_daily_steps_pages(headers=headers, start_date=start_date, user_id=user_id)
    try:
        for page_data in page_generator:
            if page_data: all_results.extend(page_data)
    except (RuntimeError, requests.exceptions.RequestException) as e:
        st.error(f"Failed to fetch daily steps data: {e}")
        logging.error(f"Error during daily steps pagination: {e}")
        return pd.DataFrame()
    
    if all_results:
        df = pd.DataFrame(all_results)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601', errors='coerce')
        #df = df[df['timestamp'].dt.date >= start_date_obj.date()]
        logging.info(f"Total daily steps records processed for user {user_id or 'self'}: {len(df)}")
        return df.sort_values(by='timestamp').reset_index(drop=True)
    else:
        logging.info("No daily steps results fetched or returned empty")
        return pd.DataFrame()
    
# --- Blood Pressure ---

@paginated_dataframe(page_size=100)
def _get_blood_pressure_pages(*, page: int, page_size: int, headers: Dict, start_date: str, user_id: Optional[int] = None) :
    """Fetches a single page of blood pressure data"""
    url = f"{API_BASE_URL}/blood-pressure/"
    params = {'start_date': start_date}
    if user_id is not None:
        params['user_id'] = user_id
    logging.debug(f"Fetching blood pressure page {page} with params: {params}") 
    return _fetch_paginated_data(url, page, page_size, headers, params)

def get_blood_pressure_data(days: int, user_id: Optional[int] = None):
    """Get ALL Blood pressure data, using the paginated fetcher."""
    start_date_obj = datetime.now() - timedelta(days=days)
    start_date = start_date_obj.strftime('%Y-%m-%d')
    headers = get_headers()
    if not headers: return pd.DataFrame()

    all_results = []
    page_generator = _get_blood_pressure_pages(headers=headers, start_date=start_date, user_id=user_id)
    try:
        for page_data in page_generator:
            if page_data: all_results.extend(page_data)
    except (RuntimeError, requests.exceptions.RequestException) as e:
        st.error(f"Failed to fetch daily steps data: {e}")
        logging.error(f"Error during daily steps pagination: {e}")
        return pd.DataFrame()
    
    if all_results:
        df = pd.DataFrame(all_results)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601', errors='coerce')
        #df = df[df['timestamp'] >= start_date_obj]
        logging.info(f"Total blood pressure records processed for user {user_id or 'self'}: {len(df)}")
        return df.sort_values(by='timestamp').reset_index(drop=True)
    else:
        logging.info(f"No blood pressure results fetched for {user_id or 'self'}.")
        return pd.DataFrame()
    
# --- Sleep Duration ---   

@paginated_dataframe(page_size=100)
def _get_sleep_duration_pages(*, page: int, page_size: int, headers: Dict, start_date: str, user_id: Optional[int] = None):
    """Fetch single page sleep duration data"""
    url = f"{API_BASE_URL}/sleep-duration/"
    params = {'start_date': start_date}
    if user_id is not None:
        params['user_id'] = user_id
    logging.debug(f"Fetching sleep duration page {page} with params: {params}")
    return _fetch_paginated_data(url, page, page_size, headers, params)

def get_sleep_duration_data(days: int = 1, user_id: Optional[int] =  None) -> pd.DataFrame:
    """Get ALL Sleep Duration data, using the paginated fetcher."""
    start_date_obj = datetime.now() - timedelta(days=days)
    start_date = start_date_obj.strftime('%Y-%m-%d')
    headers = get_headers()
    if not headers: return pd.DataFrame()

    all_results = []
    page_generator = _get_sleep_duration_pages(headers=headers, start_date=start_date, user_id=user_id)
    try:
        for page_data in page_generator:
            if page_data: all_results.extend(page_data)
    except (RuntimeError, requests.exceptions.RequestException) as e:
        st.error(f"Failed to fetch daily steps data: {e}")
        logging.error(f"Error during daily steps pagination: {e}")
        return pd.DataFrame()

    if all_results:
        df = pd.DataFrame(all_results)
        for col in ['timestamp', 'start_time', 'end_time']:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            #df = df[df['end_time'].dt.date >= start_date_obj.date()]
            logging.info(f"Total sleep duration records processed for user {user_id or 'self'}: {len(df)}")
        return df.sort_values(by='end_time').reset_index(drop=True)
    else:
        logging.info(f"No sleep duration results fetched for user {user_id or 'self'}.")
    return pd.DataFrame()

# --- SpO2 ---

@paginated_dataframe(page_size=100)
def _get_spo2_pages(*, page: int, page_size: int, headers: Dict, start_date: str, user_id: Optional[int] = None):
    """Fetches a single page of SpO2 data."""
    url = f"{API_BASE_URL}/spo2/"
    params = {'start_date': start_date}
    if user_id is not None:
        params['user_id'] = user_id
    logging.debug(f"Fetching SpO2 page {page} with params: {params}")
    return _fetch_paginated_data(url, page, page_size, headers, params)

def get_spo2_data(days: int = 1, user_id: Optional[int] = None) -> pd.DataFrame:
    """Get ALL SpO2 data, using the paginated fetcher."""
    start_date_obj = datetime.now() - timedelta(days=days)
    start_date = start_date_obj.strftime('%Y-%m-%d')
    headers = get_headers()
    if not headers: return pd.DataFrame()

    all_results = []
    page_generator = _get_spo2_pages(headers=headers, start_date=start_date, user_id=user_id)
    try:
        for page_data in page_generator:
            if page_data: all_results.extend(page_data)
    except (RuntimeError, requests.exceptions.RequestException) as e:
        st.error(f"Failed to fetch daily steps data: {e}")
        logging.error(f"Error during daily steps pagination: {e}")
        return pd.DataFrame()

    if all_results:
        df = pd.DataFrame(all_results)
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601', errors='coerce')
        #df = df[df['timestamp'] >= start_date_obj]
        return df.sort_values(by='timestamp').reset_index(drop=True)
    else:
        logging.info(f"No sleep duration results fetched for user {user_id or 'self'}.")
    return pd.DataFrame()

def get_user_list() -> Optional[pd.DataFrame]:
    """Fetches the list of users accessible by the logged-in professional."""
    url = f"{API_BASE_URL}/patients/"
    headers = get_headers()
    if not headers: return None

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        users_data = response.json()

        if isinstance(users_data, list):
            if not users_data:
                logging.info("User list endpoint returned empty list.")
                return pd.DataFrame()
            df = pd.DataFrame(users_data)
            logging.info(f"Fetched {len(df)} users.")
            return df
        elif isinstance(users_data, dict) and 'results' in users_data:
            df = pd.DataFrame(users_data['results'])
            logging.info(f"Fetched {len(df)} users (paginated response).")
            return df
        else:
            logging.error(f"Unexpected response format from user list endpoint: {users_data}")
            st.error("Received unexpected data format for user list.")
            return None
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 403:
            logging.warning("Permission denied fetching user list.")
            st.error("You do not have permission to view the patient list.")
        elif status_code == 404:
            logging.error("User list endpoint not found (404).")
            st.error("Patient list endpoint not found. Check API configuration.")
        else:
            logging.error(f"HTTP error fetching user list: {e}")
            st.error(f"API Error ({status_code}) fetching patient list.")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error fetching user list: {e}")
        st.error("Network error fetching patient list.")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error fetching user list: {e}")
        st.error("Invalid data format received for patient list.")
        return None
    except Exception as e:
        logging.exception("An unexpected error occurred fetching user list.")
        st.error("An unexpected error occurred while fetching the patient list.")
        return None