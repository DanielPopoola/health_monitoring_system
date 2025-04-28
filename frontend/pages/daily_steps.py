import streamlit as st
from utils.api import get_daily_steps_data
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import datetime
import time
import requests


refresh_interval = 30 * 1000
st_autorefresh(interval=refresh_interval, key='steps_autorefresh')

@st.cache_data(ttl=120)
def cached_get_daily_steps_data(user_identifier, days, user_id):
    print(f"CACHE MISS: Calling API for get_daily_steps_data(days={days}) for user {user_identifier}")
    return get_daily_steps_data(days=days, user_id=user_id)

def show_daily_steps_page(user_id=None):
    """
    Displays the Daily Steps page.

    Args:
        user_id (int, optional): The ID of the user whose data to display.
                                 If None, displays data for the logged-in user.
                                 Defaults to None.
    """
    if user_id:
        st.info(f"Viewing daily steps data for selected user (ID: {user_id})")
        page_title = "Patient Daily Steps"
        user_identifier_for_cache = f"user_{user_id}"
    else:
        page_title = "Your Daily Steps"
        if "email" not in st.session_state:
            st.error("User not logged in")
            st.stop()
        user_identifier_for_cache = st.session_state["email"]

    st.title(page_title)

    col1, col2 = st.columns([3, 1])
    with col1:
        time_period = st.selectbox(
            "Select time period:",
            ["Last 7 days", "Last 14 days", "Last 30 days", "Last 60 days", "Custom range"],
            key=f"steps_time_period_{user_identifier_for_cache}" # Unique key per user view
        )
    with col2:
        refresh_button = st.button("Refresh Data", key=f"steps_refresh_{user_identifier_for_cache}")

    if time_period == "Custom range":
        col1_date, col2_date = st.columns(2)
        today = datetime.date.today()
        with col1_date:
            start_date = st.date_input("Start date", today - datetime.timedelta(days=7), key=f"steps_start_{user_identifier_for_cache}")
        with col2_date:
            end_date = st.date_input("End date", today, key=f"steps_end_{user_identifier_for_cache}")
        days = (end_date - start_date).days + 1
    else:
        days = {"Last 7 days": 7, "Last 14 days": 14, "Last 30 days": 30, "Last 60 days": 60}[time_period]

    if refresh_button:
        with st.spinner("Refreshing data..."):
            cached_get_daily_steps_data.clear()
            st.rerun()

    with st.spinner("Fetching daily steps data..."):
        steps_df = cached_get_daily_steps_data(user_identifier_for_cache, days, user_id=user_id)

    if steps_df.empty:
        st.warning("No daily steps data available for the selected period. Have you synced your device?")
        st.stop()

    st.subheader("Steps Summary")
    col1, col2, col3 = st.columns(3)

    latest_entry = steps_df.iloc[-1]
    latest_steps = latest_entry['count']
    latest_goal = latest_entry.get('goal', 10000)
    latest_date = latest_entry['timestamp']

    with col1:
        st.metric("Latest Steps", f"{latest_steps:,}", help=f"Recorded on {latest_date}")
        if latest_goal and latest_steps >= latest_goal:
            st.success(f"Goal ({latest_goal:,}) Reached! 🎉")
        elif latest_goal:
            st.info(f"Goal: {latest_goal:,}")
        else:
            st.caption("No goal set for this entry")

    with col2:
        avg_steps = steps_df['count'].mean()
        st.metric("Average Daily Steps", f"{avg_steps:.0f}", help=f"Average over selected {days} days")
        if latest_goal:
            avg_goal_percent = (avg_steps / latest_goal ) * 100 if latest_goal > 0 else 0
            st.progress(int(avg_goal_percent))
            st.caption(f"{avg_goal_percent:.1f}% of latest goal ({latest_goal:,}) on average")

    with col3:
        total_steps = steps_df['count'].sum()
        st.metric("Total steps", f"{total_steps}", help=f"Total over selected {days} days")
        days_with_data = steps_df['timestamp'].dt.date.nunique()
        st.caption(f"Data recorded on {days_with_data} of the {days} days.")

    # Steps Trend Chart
    st.subheader("Daily Steps Trend")
    plot_daily_steps_trend(steps_df, latest_goal)


    if (st.session_state["access_token"] and not user_id) or (st.session_state["access_token"] and user_id):
        st.subheader("Weekly Average Analysis")
        run_weekly_average_analysis(user_id)


def plot_daily_steps_trend(df: pd.DataFrame, goal: int | None):
    """Plots the daily steps trend using a bar chart."""
    fig = px.bar(df, x='timestamp', y='count',
                labels={'timestamp': 'Date', 'count': 'Steps Count'},
                title="Daily Steps Over Time")
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Steps",
        hovermode="x unified",
        bargap=0.2,
    )
    fig.update_traces(marker_color='#1f77b4',
                    hovertemplate='<b>Date</b>: %{x|%Y-%m-%d}<br><b>Steps</b>: %{y:,}<extra></extra>')
    
    if goal and goal > 0:
        fig.add_hline(y=goal, line_dash="dash",line_color="red",
                    annotation_text=f"Goal: {goal:,}",
                    annotation_position="bottom right")
        
    st.plotly_chart(fig, use_container_width=True)

def run_weekly_average_analysis(user_id=None):
    """Calls the backend endpoint for weekly average analysis and displays results."""
    API_BASE_URL = "http://localhost:8000/api"
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    endpoint_url = f"{API_BASE_URL}/daily-steps/weekly_average/"

    params = {}
    if user_id:
        params['user_id'] = user_id

    with st.spinner("Analyzing weekly average..."):
        try:
            response = requests.get(endpoint_url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()

            avg = data.get('weekly_average')
            completeness = data.get('data_completeness', 0)
            goal_metrics = data.get('goal_metrics', {})
            current_goal = goal_metrics.get('current_goal')
            avg_goal_percent = goal_metrics.get('average_percentage')

            if avg is not None:
                st.metric("7-Day Average Steps", f"{avg:,.0f}")
                st.progress(int(completeness))
                st.caption(f"Data completeness: {completeness:.1f}% for the last 7 days.")

                if current_goal:
                    st.metric("Average vs Goal", f"{avg_goal_percent:.1f}%",
                              help=f"Based on the latest goal of {current_goal:,} steps.")
                    if goal_metrics.get('meeting_goal'):
                        st.success("On average, you're meeting your latest daily goal over the past week!")
                    else:
                        st.info("Keep pushing to meet your daily goal average")
                else:
                    st.caption("No goal data found for comparison")

            else:
                st.info("Not enough data to calculate the weekly average.")
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to retrieve weekly average analysis. Error {e}")
        except Exception as e:
            st.error(f"An unexpected error occured: {e}")
