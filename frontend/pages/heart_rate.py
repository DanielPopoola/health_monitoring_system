import streamlit as st
from utils.api import get_heart_rate_data 
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import requests
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta, timezone
import logging
import time


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


refresh_interval = 10 * 1000
st_autorefresh(interval=refresh_interval, key="hr_autorefresh")
ALLOWED_ROLES = ['DOCTOR', 'NURSE', 'ADMIN']

@st.cache_data(ttl=60)
def cached_get_heart_rate_data(user_identifier: str, fetch_days: int, fetch_hours: int, user_id: int | None = None) -> pd.DataFrame:
    """
    Fetches heart rate data from the API, cached based on user and fetch range.
    Args:
        user_identifier: A unique string identifying the cache entry (e.g., email or user_id).
        fetch_days: Number of days back to request data for (initial fetch).
        fetch_hours: Number of hours back to request data for (initial fetch).
        user_id: Optional ID of the patient being viewed.
    Returns:
        Pandas DataFrame with heart rate data.
    """
    print(f"CACHE MISS: Calling API get_heart_rate_data(days={fetch_days}, hours={fetch_hours}) for user {user_identifier}")
    return get_heart_rate_data(days=fetch_days, hours=fetch_hours, user_id=user_id)

def show_heart_rate_page(user_id=None):
    """Displays the Heart Rate Monitoring page"""
    current_role = st.session_state.get("role", "USER")
    if current_role not in ALLOWED_ROLES:
        if not user_id and current_role == 'USER':
            pass
        elif user_id:
            st.error("🚫 Access Denied: You do not have permission to view patient data.")
            st.stop()

    page_title = "Heart Rate Monitoring"
    user_identifier_for_cache = st.session_state.get("email", "guest")

    if user_id:
        page_title = f"Patient Heart Rate (ID: {user_id})"
        st.info(f"Viewing Heart Rate data for selected user (ID: {user_id})")
        user_identifier_for_cache = f"user_{user_id}"
    elif "first_name" in st.session_state and st.session_state["first_name"]:
        st.subheader(f"Hello, {st.session_state["first_name"]}")

    st.title(page_title)

    col1, col2 = st.columns([3, 1])
    with col1:
        time_period = [
                "Last hour", "Last 6 hours", "Last 12 hours", # Hourly options
                "Last 24 hours", "Last 3 days", "Last 7 days", # Daily options
                "Last 30 days", "Custom range"
            ]
        selected_period = st.selectbox(
            "Select time period:",
            options=time_period,
            index=3, # Default to "  Last 24 hours",
            key=f"hr_time_period_{user_identifier_for_cache}"
        )

    with col2:
        refresh_button = st.button("Refresh Data", key=f"hr_refresh_{user_identifier_for_cache}")

    now_aware = datetime.now(timezone.utc)
    end_dt_for_filter = now_aware # Default end time is now

    fetch_days = 1
    fetch_hours = 0

    if selected_period == "Custom range":
        col1date, col2date = st.columns(2)
        with col1date:
            start_date = st.date_input(
                "Start date ",
                now_aware.date(),
                key=f"hr_start_date_{user_identifier_for_cache}"
            )
            start_time = st.time_input(
                "Start time",
                now_aware.time().replace(second=0, microsecond=0),
                key=f"hr_start_time_{user_identifier_for_cache}"
            )
        with col2date:
            end_date = st.date_input(
                "End date",
                now_aware.date(),
                key=f"hr_end_date_{user_identifier_for_cache}"
            )
            end_time = st.time_input(
                "End time",
                now_aware.time().replace(second=0, microsecond=0),
                key=f"hr_end_time_{user_identifier_for_cache}"
            )

        try:
            start_dt_for_filter  = datetime.combine(start_date, start_time).replace(tzinfo=timezone.utc)
            end_dt_for_filter = datetime.combine(end_date, end_time).replace(tzinfo=timezone.utc)
        except Exception as e:
            st.error(f"Invalid datetime input: {e}")
            logging.exception("Exception during datetime operation")
            st.stop()

        fetch_delta = end_dt_for_filter - start_dt_for_filter
        fetch_days = fetch_delta.days  + (1 if fetch_delta.seconds > 0 or fetch_delta.microseconds > 0 else 0)
        fetch_hours  = 0
        time_description = f"Custom: {start_dt_for_filter.strftime('%Y-%m-%d %H:%M')} to {end_dt_for_filter.strftime('%Y-%m-%d %H:%M')}"
    else:
        period_deltas = {
        "Last hour": timedelta(hours=1),
        "Last 6 hours": timedelta(hours=6),
        "Last 12 hours": timedelta(hours=12),
        "Last 24 hours": timedelta(days=1),
        "Last 3 days": timedelta(days=3),
        "Last 7 days": timedelta(days=7),
        "Last 30 days": timedelta(days=30)
        }
        time_delta = period_deltas.get(selected_period, timedelta(days=1))
        start_dt_for_filter = now_aware - time_delta
        time_description = selected_period

        fetch_days = time_delta.days
        fetch_hours = time_delta.seconds // 3600

        if fetch_days == 0 and fetch_hours > 0:
             fetch_days = 1 
             fetch_hours = 0

    if refresh_button:
        with st.spinner("Refreshing data..."):
            cached_get_heart_rate_data.clear()
            st.rerun()

    heart_rate_df_raw = pd.DataFrame()

    is_authenticated = "access_token" in st.session_state and st.session_state["access_token"]
    can_fetch = is_authenticated or user_id
    
    if can_fetch:
        with st.spinner(f"Fetching heart rate data ({time_description})..."):
            try:
                heart_rate_df_raw = cached_get_heart_rate_data(user_identifier=user_identifier_for_cache,
                                                           fetch_days=fetch_days,
                                                           fetch_hours=fetch_hours,
                                                           user_id=user_id)
            except Exception as e:
                st.error(f"Error fetching heart rate data: {e}")
                logging.exception("Exception during cached_get_heart_rate_data call")
                heart_rate_df_raw = pd.DataFrame()

    # Perform precise client-side filtering AFTER fetching/retrieving from cache
    if not heart_rate_df_raw.empty:
        if not pd.api.types.is_datetime64_any_dtype(heart_rate_df_raw['timestamp']):
            st.warning("Timestamp column is not in datetime format. Attempting conversion.")
            heart_rate_df_raw['timestamp'] = pd.to_datetime(heart_rate_df_raw['timestamp'], format='ISO8601', errors='coerce')

        heart_rate_df_raw = heart_rate_df_raw.dropna(subset=['timestamp'])

        try:
            df_timestamp_utc = heart_rate_df_raw['timestamp'].dt.tz_convert(timezone.utc)
            heart_rate_df = heart_rate_df_raw[
                (df_timestamp_utc >= start_dt_for_filter) &
                (df_timestamp_utc <= end_dt_for_filter)
            ].copy()
            logging.info(f"Filtered raw data ({len(heart_rate_df_raw)}) to {len(heart_rate_df)} records for period: \
                        {start_dt_for_filter} to {end_dt_for_filter}")
        except TypeError as te:
            st.error("Error comparing timestamps. Check timezone consistency.")
            logging.exception(f"TypeError during timestamp filtering: {te}")
            heart_rate_df = pd.DataFrame()
        except Exception as e:
            st.error(f"An unexpected error occurred during data filtering: {e}")
            logging.exception("Exception during data filtering")
            heart_rate_df = pd.DataFrame()
    else:
        heart_rate_df = pd.DataFrame()


    if heart_rate_df.empty:
        st.warning("No heart rate data available for the selected period. Please check your connection or try another time range.")
        st.stop()

    st.subheader("Heart Rate Summary")
    col_summary1, col_summary2, col_summary3 = st.columns(3)

    with col_summary1:
        latest_hr = heart_rate_df.iloc[-1]['value']
        hr_status = get_hr_status(latest_hr) 
        color = get_hr_color(hr_status)  

        st.metric("Latest Heart Rate", f"{latest_hr} BPM")
        st.markdown(f"<p style='color:{color}; font-weight:bold;'>{hr_status}</p>", unsafe_allow_html=True)

    with col_summary2:
        avg_hr = heart_rate_df['value'].mean()
        st.metric(
            "Average Heart Rate",
            f"{avg_hr:.0f} BPM",
            help=f"Average over the selected period ({time_description})" # Dynamic help text
        )
        st.caption(f"Based on {len(heart_rate_df)} readings")

    with col_summary3:
        min_hr = heart_rate_df['value'].min()
        max_hr = heart_rate_df['value'].max()
        st.metric("Range", f"{min_hr:.0f} - {max_hr:.0f} BPM")
        variability = heart_rate_df['value'].std()
        st.metric("Variability (Std Dev)", f"{variability:.1f} BPM", help="Standard deviation over the period")

    # Heart Rate Chart
    st.subheader("Heart Rate Trend")
    plot_heart_rate_trend(heart_rate_df)


    if 'activity_level' in heart_rate_df.columns:
        activity_levels = sorted(heart_rate_df['activity_level'].unique())
        if len(activity_levels) > 1:
            activity_key = f"hr_activity_filter_{user_identifier_for_cache}"
            selected_activity = st.multiselect(
                "Filter by activity level:",
                options=activity_levels,
                default=activity_levels,
                key=activity_key
            )

            if selected_activity:
                filtered_df_activity = heart_rate_df[heart_rate_df['activity_level'].isin(selected_activity)]
                st.subheader("Heart Rate by Selected Activity Level")
                if not filtered_df_activity.empty:
                     plot_heart_rate_by_activity(filtered_df_activity)
                else:
                    st.info("No data for the selected activity level(s) in this time period.")
            else:
                st.warning("Please select at least one activity level to filter.")

    # HRV Analysis
    if "access_token" in st.session_state and len(heart_rate_df) > 10:
        st.divider()
        st.subheader("Heart Rate Variability (HRV)")
        run_hrv_analysis()

    # Baseline comparison
    if "access_token" in st.session_state and len(heart_rate_df) > 10:
        st.divider()
        st.subheader("Baseline comparison")
        run_baseline_comparison()

    if "access_token" in st.session_state:
        st.divider()
        st.subheader("Resting Heart Rate")
        run_resting_analysis()


def plot_heart_rate_trend(df: pd.DataFrame):
    fig = go.Figure()

    # Add heart rate trace
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['value'],
        name='Heart Rate',
        line=dict(color='#F63366', width=2),
        mode='lines+markers'
    ))               

    # Add reference zones
    y_min = max(40, df['value'].min() - 10)
    y_max =  min(200, df['value'].max() + 10)
    
    # Sleeping zone
    fig.add_shape(
        type="rect",
        x0=df['timestamp'].min(),
        x1=df['timestamp'].max(),
        y0=50,
        y1=85,
        fillcolor="rgba(173, 216, 230, 0.25)",
        line=dict(width=0),
        layer="below"
    )
    # Rest zone
    fig.add_shape(
        type="rect",
        x0=df['timestamp'].min(),
        x1=df['timestamp'].max(),
        y0=60,
        y1=100,
        fillcolor="rgba(144, 238, 144, 0.2)",
        line=dict(width=0),
        layer="below"
    )
    # Active zone
    fig.add_shape(
        type="rect",
        x0=df['timestamp'].min(),
        x1=df['timestamp'].max(),
        y0=60,
        y1=120,
        fillcolor="rgba(255, 165, 0, 0.25)",
        line=dict(width=0),
        layer="below"
    )
    # Update layout
    fig.update_layout(
        title="Heart Rate Over Time",
        xaxis_title="Date & Time",
        yaxis_title="Heart Rate (BPM)",
        yaxis=dict(range=[y_min, y_max]),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=20, r=20, t=50, b=50),
        height=450,
        hovermode="x unified"
    )

    # Add annotation for normal range
    fig.add_annotation(
        x=df['timestamp'].max(),
        y=80,
        text="Normal Resting (60-100 BPM)",
        showarrow=False,
        yshift=0,
        xshift=-5,
        align="right",
        font=dict(size=10, color="rgba(0, 128, 0, 0.8)")
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_heart_rate_by_activity(df: pd.DataFrame):
    if 'activity_level' not in df.columns or df.empty:
        st.info("Activity level data not available")
        return
    
    # Create box plot by activity level
    fig = px.box(
        df,
        x='activity_level',
        y='value',
        color='activity_level',
        title='Heart Rate Distribution by Activity level',
        labels={'value': 'Heart Rate (BPM)', 'activity_level': 'Activity Level'}
    )

    fig.update_layout(
        height=400,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # Calculate and show stats
    activity_stats = df.groupby('activity_level')['value'].agg(['mean', 'min', 'max']).reset_index()
    activity_stats.columns = ['Activity Level', 'Average BPM', 'Minimum BPM', 'Maximum BPM']
    activity_stats = activity_stats.round(1)

    st.write("Heart Rate Statistics by Activity Level:")
    st.dataframe(activity_stats, hide_index=True)

def run_hrv_analysis():
    # Call the HRV endpoint and display results
    API_BASE_URL = "http://localhost:8000/api"
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}

    col1, col2 = st.columns([4, 1])
    with col2:
        time_window = st.selectbox("Time window (hours)", [1, 2, 4, 8, 12, 24], index=2)

    with st.spinner("Calculating heart rate variablity..."):
        response = requests.get(
            f"{API_BASE_URL}/heart-rate/hrv/?time_window={time_window}", headers=headers
        )

        if response.status_code == 200:
            data = response.json()

            if "message" in data:
                st.info(data["message"])
            elif "hrv" in data:
                hrv_value = data['hrv']
                st.metric("Heart Rate Variablity", f"{hrv_value} ms")

            if hrv_value < 20:
                st.warning("Low HRV may indicate stress or health issues.")
            elif 20 <= hrv_value < 50:
                st.info("Moderate HRV is common during regular daily activities")
            else:
                st.success("High HRV often indicates good cardiovascular health")

            st.caption(f"Based on data from the past {time_window} hour(s)")
        else:
            st.error("Failed to retrieve HRV data")

def run_baseline_comparison():
    # Call the baseline comparison endpoint and display results
    API_BASE_URL = "http://localhost:8000/api"
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}

    col1, col2 = st.columns([3, 2])
    with col1:
        baseline_days = st.slider("Baseline period (days)", 7, 90, 30)

    with col2:
        baseline_activity =  st.selectbox(
            "Activity level filter",
            ["sleeping", "resting", "active"],
            index=0
        )
    
    # Convert "all" to None for the API
    activity_param = None if baseline_activity == "all" else baseline_activity

    with st.spinner("Comparing to baseline..."):
        response = requests.get(
            f"{API_BASE_URL}/heart-rate/baseline_comparison/?baseline_days={baseline_days}&baseline_activity={activity_param}",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()

            if "message" in data:
                st.info(data["message"])
            else:
                # Extract comparison data
                current_hr = data.get('current', 0)
                baseline_hr = data.get('baseline', 0)
                percent_change = data.get('percent_change', 0)
                is_significant = data.get('is_significant', False)

                # Format the delta display
                delta_format = f"{percent_change:+.1f}%" if percent_change else None
                delta_color = "normal"

                if percent_change > 5:
                    delta_color = "off" if is_significant else "normal"
                elif percent_change < -5:
                    delta_color = "inverse"  if is_significant else "normal"

                # Display metrics
                st.metric(
                    "Current vs Baseline",
                    f"{current_hr:.1f} BPM",
                    delta=delta_format,
                    delta_color=delta_color,
                    help="Comparison with your baseline heart rate"
                )

                # Display interpretation
                if is_significant:
                    if percent_change > 5:
                        st.warning(f"Your heart rate is significantly higher ({percent_change:.1f}%) than your {baseline_days}-day baseline")
                    elif percent_change < -5:
                        st.success(f"Your heart rate is significantly lower ({percent_change:.1f}%) than your {baseline_days}-day baseline")
                else:
                    st.info(f"Your heart rate is within normal variation of your {baseline_days}-day baseline")
        else:
            st.error("Failed to retrieve baseline comparison data.")

def run_resting_analysis():
    # Call the baseline comparison endpoint and display results
    API_BASE_URL = "http://localhost:8000/api"
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}

    with st.spinner("Calculating resting heart rate..."):
        response = requests.get(
            f"{API_BASE_URL}/heart-rate/resting_average/",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()

            if "error" in data:
                st.info("Not enough resting heart rate data available")
            else:
                avg_resting_hr = data.get("Average_resting_heart_rate", 0)

                # Create a gauge chart for resting heart rate
                fig = create_hr_gauge(avg_resting_hr)
                st.plotly_chart(fig, use_container_width=True)

                # Provide interpretation based on resting heart rate
                if avg_resting_hr < 60:
                    st.info("Your resting heart rate is below 60 BPM, which may indicate good cardiovascular fitness")
                elif 60 <= avg_resting_hr <= 100:
                    st.success("Your resting heart rate is within the normal range (60-100 BPM)")
                else:
                    st.warning("Your resting heart rate is above 100 BPM, which may require attention")
        else:
            st.error("Failed to retrieve resting heart rate data")

def create_hr_gauge(value):
    # Create a gauge chart for heart rate
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain = {'x' : [0, 1], 'y':[0, 1]},
        title={'text': "Resting Heart Rate", 'font': {'size': 24}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkgray"},
            'bar': {'color': "blue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 60], 'color': '#4ecdc4'},     # Critical
                {'range': [60, 100], 'color': '#ffe66d'},    # Normal
                {'range': [100, 120], 'color': '#ff6b6b'}    # Critical
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))

    return fig
    

def get_hr_status(value):
    if value < 60:
        return 'Below Normal'
    elif value <= 100:
        return 'Normal'
    elif value <= 140:
        return 'Fat Burn'
    elif value <= 170:
        return 'Cardio'
    else:
        return 'Peak'

def get_hr_color(zone):
    colors = {
        "Below Normal": "#64B5F6",    # Light Blue
        "Normal": "#4CAF50",          # Green
        "Fat Burn": "#FFC107",        # Yellow
        "Cardio": "#FF5722",          # Orange
        "Peak": "#F44336",            # Red
        "Unknown": "#9E9E9E"          # Grey fallback
    }
    return colors.get(zone, "#9E9E9E")