import streamlit as st
from utils.api import get_sleep_duration_data
import plotly.graph_objects as go
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import datetime
import requests
import time

refresh_interval = 10 * 60 * 1000
st_autorefresh(interval=refresh_interval, key="sleep_autorefresh")

@st.cache_data(ttl=300)
def cached_get_sleep_duration(user_identifier, days, user_id=None):
    print(f"CACHE MISS: Calling API for get_sleep_duration_data(days={days}) for user {user_identifier}")
    return get_sleep_duration_data(days, user_id=user_id)

def show_sleep_duration_page(user_id=None):
    """
    Displays the Sleep Duration page.

    Args:
        user_id (int, optional): The ID of the user whose data to display.
                                 If None, displays data for the logged-in user.
                                 Defaults to None.
    """
    if user_id:
        st.info(f"Viewing Sleep Duration data for selected user (ID: {user_id})")
        page_title = "Patient Sleep Duration"
        user_identifier_for_cache = f"user_{user_id}"
    else:
        page_title  = "Your Sleep Duration"
        if "email" not in st.session_state:
            st.error("User is not logged in.")
            st.stop()
        user_identifier_for_cache = st.session_state["email"]

    st.title(page_title)

    user_age = None
    if user_id:
        # If viewing a patient, we might need to fetch their age separately
        user_age = st.number_input("Enter Patient's Age for Analysis", min_value=1, max_value=120, value=30, 
                                   step=1, key=f"sleep_age_input_{user_identifier_for_cache}")
    elif "age" in st.session_state and st.session_state["age"]:
        user_age = st.session_state["age"]
    else:
        user_age = st.number_input("Enter Your Age for Analysis", min_value=1, max_value=120, value=st.session_state.get("age", 30), 
                                   step=1, key=f"sleep_age_input_{user_identifier_for_cache}")
        st.session_state["age"] = user_age

    
    col1, col2 = st.columns([3, 1])
    with col1:
        time_period = st.selectbox(
            "Select time period:",
            ["Last 7 nights", "Last 14 nights", "Last 30 nights", "Last 60 nights", "Custom range"],
            key=f"sleep_time_period_{user_identifier_for_cache}"
        )
    with col2:
        refresh_button = st.button("Refresh Data", key=f"sleep_refresh_{user_identifier_for_cache}")

    if time_period == "Custom range":
        col1_date, col2_date = st.columns(2)
        today = datetime.date.today()
        with col1_date:
            default_start = today - datetime.timedelta(days=7)
            start_date = st.date_input("Start date (night ending)", default_start, key=f"sleep_start_{user_identifier_for_cache}")
        with col2_date:
            end_date = st.date_input("End date (night ending)", today, key=f"sleep_end_{user_identifier_for_cache}")
        days = (end_date - start_date) + 1
    else:
        days = {"Last 7 nights": 7, "Last 14 nights": 14, "Last 30 nights": 30, "Last 60 nights": 60}[time_period]

    if refresh_button:
        with st.spinner("Refreshing data..."):
            cached_get_sleep_duration.clear()
            st.rerun()

    with st.spinner("Fetching sleep data..."):
        sleep_df = cached_get_sleep_duration(user_identifier_for_cache, days, user_id=user_id)

    if sleep_df.empty:
        st.warning("No sleep data available for selected period.")
        st.stop()

    # Display summmary metrics
    st.subheader("Sleep Session Summary")
    col1_summary, col2_summary, col3_summary = st.columns(3)

    latest_entry = sleep_df.iloc[-1]
    latest_duration = latest_entry['duration']
    latest_quality = latest_entry['quality']
    latest_interruptions = latest_entry['interruptions']
    latest_end_time = pd.to_datetime(latest_entry['end_time']).strftime('%Y-%m-%d %H:%M')

    with col1_summary:
        st.metric("Sleep Duration", f"{latest_duration:.1} hrs", help=f"Ended on {latest_end_time}")
        if latest_quality:
            quality_desc = "Poor" if latest_quality < 5 else "Fair" if latest_quality < 8 else "Good"
            st.metric("Latest Quality", f"{latest_quality}/10 ({quality_desc})", help="Self-reported quality score")

    with col2_summary:
        avg_duration = sleep_df['duration'].mean()
        st.metric("Average Duration", f"{avg_duration:.1f} hrs", help=f"Average sleep over selected {days} nights")
        avg_quality = sleep_df['quality'].mean() if 'quality' in sleep_df and not sleep_df['quality'].isnull().all() else None
        if avg_quality:
            st.metric("Average Quality", f"{avg_quality:.1f}/10")

    with col3_summary:
        total_sleep_time = sleep_df['duration'].sum()
        st.metric("Total Sleep Time", f"{total_sleep_time:.1f} hrs", help=f"Total sleep duration over selected {days} nights")
        if latest_interruptions is not None:
            st.metric("Latest Interruptions", f"{latest_interruptions}", help="Number of interruptions during latest sleep")

    # Sleep Duration and Chart
    st.subheader("Sleep Duration Chart")
    plot_sleep_duration_trend(sleep_df)

    api_token = st.session_state.get("access_token")
    if (api_token and not user_id) or (api_token and user_id):
        st.divider()
        col_analysis1, col_analysis2 = st.columns(2)

        with col_analysis1:
            st.subheader("Sleep Sufficiency Check")
            if user_age:
                run_sufficiency_check(user_age,user_id=user_id)
            else:
                st.warning("Please enter age above to run sufficiency check.")
            
        with col_analysis2:
            st.subheader(f"{days}-Night Average Analysis")
            run_weekly_average_sleep(days, user_age, user_id=user_id)

def plot_sleep_duration_trend(df: pd.DataFrame):
    """Plots the sleep duration trend using a bar chart."""
    df['date'] = pd.to_datetime(df['timestamp']).dt.date

    fig = px.bar(df, x='date', y='duration',
                labels={'date': 'Night Ending on', 'duration': 'Sleep Duration (hrs)'},
                title="Sleep Duration Over Time")
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Duration (hours)",
        hovermode="x unified",
        bargap=0.3,
    )
    fig.update_traces(marker_color='#9467bd', # Purple color for sleep
                       hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br><b>Duration</b>: %{y:.1f} hrs<extra></extra>')
    
    fig.add_hrect(y0=7, y1=9, line_width=0, fillcolor="green", opacity=0.1,
                  annotation_text="Recommended (Adult: 7-9 hrs)", annotation_position="top left")
    
    st.plotly_chart(fig, use_container_width=True)

def run_sufficiency_check(age: int, user_id=None):
    API_BASE_URL = "http://localhost:8000/api"
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    endpoint_url = f"{API_BASE_URL}/sleep-duration/sufficiency_check/"
    params = {'age': age}
    if user_id:
        params['user_id'] = user_id

    with st.spinner("Checking sleep sufficiency..."):
        try:
            response = requests.get(endpoint_url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            is_sufficient = data.get('is_sufficient')
            duration = data.get('duration')
            recommendation = data.get('recommendation', 'No specific recommendation provided.')
            rec_range = data.get('recommended_range', {})
            min_h = rec_range.get('min_hours')
            max_h = rec_range.get('max_hours')

            if is_sufficient is not None and duration is not None:
                st.metric("Latest Sleep Duration", f"{duration:.1f} hrs")
                if is_sufficient:
                    st.success(f"✅ Sufficient sleep based on age {age}.")
                else:
                    st.warning(f"⚠️ Sleep duration may be insufficient/excessive for age {age}.")

                if min_h and max_h:
                    st.caption(f"Recommended range for age {age}: {min_h}-{max_h} hours.")
                
                st.info(f"Recommendation: {recommendation}")

            else:
                st.info("Could not determine sufficiency from the latest data.")
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to retrieve sufficiency check. Error: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

def run_weekly_average_sleep(days: int, age: int = None, user_id=None):
    API_BASE_URL = "http://localhost:8000/api"
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    endpoint_url = f"{API_BASE_URL}/sleep-duration/weekly_average/"

    params = {'days': days}
    if age:
        params['age'] = age
    if user_id:
        params['user_id'] = user_id

    with st.spinner(f"Analyzing {days}-Days average sleep sessions..."):
        try:
            respone = requests.get(endpoint_url, headers=headers, params=params)
            respone.raise_for_status()

            data = respone.json()
            avg = data.get('weekly_average')
            completeness = data.get('data_completeness', 0)
            assessment = data.get('assessment', 'Assessment not available.')
            rec_range = data.get('recommended_range', {})
            min_h = rec_range.get('min_hours')
            max_h = rec_range.get('max_hours')

            if avg is not None:
                st.metric(f"{days}-Night Average Duration", f"{avg:.1f} hrs")
                st.progress(int(completeness))
                st.caption(f"Data completeness: {completeness:.1f}% for the last {days} nights.")
                st.info(f"Assessment: {assessment}")
                if min_h and max_h:
                    st.caption(f"Weekly target range: {min_h}-{max_h} hrs (based on age if provided).")
            else:
                st.info(data.get("message", f"Not enough data to calculate the {days}-night average."))
        
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to retrieve {days}-night average sleep. Error: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

