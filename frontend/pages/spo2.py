import streamlit as st
from utils.api import get_spo2_data
import plotly.graph_objects as go
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta
import requests
import time


refresh_interval = 15 * 1000
st_autorefresh(interval=refresh_interval, key="spo2_autorefresh")


@st.cache_data(ttl=60) # Cache for 1 minute
def cached_get_spo2_data(user_identifier, days, user_id=None):
    print(f"CACHE MISS: Calling API for get_spo2_data(days={days}) for user {user_identifier}")
    return get_spo2_data(days, user_id=user_id)

def show_spo2_page(user_id=None):
    """
    Displays the SpO2 (Blood Oxygen) page.

    Args:
        user_id (int, optional): The ID of the user whose data to display.
                                 If None, displays data for the logged-in user.
                                 Defaults to None.
    """
    if user_id:
        st.info(f"Viewing SpO2 data for selected user (ID: {user_id})")
        page_title = "Patient Blood Oxygen (SpO2)"
        user_identifier_for_cache = f"user_{user_id}"
    else:
        page_title = "Your Blood Oxygen (SpO2)"
        if "email" not in st.session_state:
            st.error("User not logged in.")
            st.stop()
        user_identifier_for_cache = st.session_state["email"]

    st.title(page_title)

    col1, col2 = st.columns([3, 1])
    with col1:
        time_period = st.selectbox(
            "Select time period:",
            ["Last hour", "Last 6 hours", "Last 24 hours", "Last 3 days", "Last 7 days", "Custom range"],
            index=2, # Default to Last 24 hours
            key=f"spo2_time_period_{user_identifier_for_cache}"
        )

    with col2:
        refresh_button = st.button("Refresh Data", key=f"spo2_refresh_{user_identifier_for_cache}")

    now = datetime.now()
    if time_period == "Custom range":
        col1_date, col2_date = st.columns(2)
        with col1_date:
            start_dt = st.date_input("Start date/time", now - timedelta(days=1), key=f"spo2_start_{user_identifier_for_cache}")
        with col2_date:
            end_dt = st.date_input("End date/time", now, key=f"spo2_end_{user_identifier_for_cache}")
        if start_dt > end_dt:
            st.error("Error: Start date/time must be before or equal to end date/time.")
            st.stop()
        days = (end_dt - start_dt).days + 1
    else:
        time_deltas = {
            "Last hour": timedelta(hours=1),
            "Last 6 hours": timedelta(hours=6),
            "Last 24 hours": timedelta(days=1),
            "Last 3 days": timedelta(days=3),
            "Last 7 days": timedelta(days=7)
        }
        # Calculate days needed for the API call (use ceiling)
        delta = time_deltas[time_period]
        days = (delta.days + (1 if delta.seconds > 0 else 0)) if delta else 1


    if refresh_button:
        with st.spinner("Refreshing data..."):
            cached_get_spo2_data.clear()
            st.rerun()

    # Fetch data
    with st.spinner("Fetching SpO2 data..."):
        spo2_df = cached_get_spo2_data(user_identifier_for_cache, days, user_id=user_id)

        if time_period != "Custom range":
            start_dt_filter = now - time_deltas[time_period]
            #spo2_df = spo2_df[spo2_df['timestamp'] >= start_dt_filter]
        elif 'start_dt' in locals() and 'end_dt' in locals(): # Check if custom dates were set
             spo2_df = spo2_df[(spo2_df['timestamp'] >= start_dt) & (spo2_df['timestamp'] <= end_dt)]


    if spo2_df.empty:
        st.warning("No SpO2 data available for the selected period.")
        st.stop()

    # Display summary metrics
    st.subheader("SpO2 Summary")
    col_summary1, col_summary2, col_summary3 = st.columns(3)

    latest_entry = spo2_df.iloc[-1]
    latest_spo2 = latest_entry['value']
    latest_time = pd.to_datetime(latest_entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')

    with col_summary1:
        fig_gauge = create_spo2_gauge(latest_spo2)
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.metric("Latest SpO2", f"{latest_spo2}%", help=f"Recorded at {latest_time}")
        severity = get_spo2_severity(latest_spo2)
        color = get_spo2_color(severity)
        st.markdown(f"<p style='color:{color}; font-weight:bold;'>Status: {severity}</p>", unsafe_allow_html=True)


    with col_summary2:
        avg_spo2 = spo2_df['value'].mean()
        st.metric("Average SpO2", f"{avg_spo2:.1f}%", help=f"Average over the selected period")
        min_spo2 = spo2_df['value'].min()
        st.metric("Minimum SpO2", f"{min_spo2}%", delta=f"{min_spo2 - avg_spo2:.1f}% vs Avg", delta_color="inverse")


    with col_summary3:
        max_spo2 = spo2_df['value'].max()
        st.metric("Maximum SpO2", f"{max_spo2}%", delta=f"{max_spo2 - avg_spo2:.1f}% vs Avg", delta_color="normal")
        reading_count = len(spo2_df)
        st.caption(f"Based on {reading_count} readings in the period.")


    # SpO2 Trend Chart
    st.subheader("SpO2 Trend")
    plot_spo2_trend(spo2_df)

    # --- Custom Endpoint Calls ---
    api_token = st.session_state.get("access_token")
    if (api_token and not user_id) or (api_token and user_id):
        st.divider()
        col_analysis1, col_analysis2 = st.columns(2)

        with col_analysis1:
            st.subheader("Lowest Reading Check")
            run_lowest_reading_analysis(user_id=user_id)

        with col_analysis2:
            st.subheader("Alert Check")
            run_alert_check(user_id=user_id)


def get_spo2_severity(value):
    if value >= 95: return "Normal"
    elif value >= 90: return "Mild Hypoxemia"
    elif value >= 80: return "Moderate Hypoxemia"
    else: return "Severe Hypoxemia"

def get_spo2_color(severity):
    colors = {
        "Normal": "#4CAF50",            # Green
        "Mild Hypoxemia": "#FFC107",    # Yellow
        "Moderate Hypoxemia": "#FF9800",# Orange
        "Severe Hypoxemia": "#F44336",  # Red
    }
    return colors.get(severity, "#9E9E9E")

def create_spo2_gauge(value):
    """Creates a Plotly gauge chart for SpO2."""
    severity = get_spo2_severity(value)
    color = get_spo2_color(severity)

    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        title = {'text': f"Latest SpO2 (%)<br><span style='font-size:0.8em;color:{color}'>{severity}</span>"},
        domain = {'x': [0, 1], 'y': [0, 1]},
        gauge = {
            'axis': {'range': [70, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [70, 80], 'color': get_spo2_color("Severe Hypoxemia")},
                {'range': [80, 90], 'color': get_spo2_color("Moderate Hypoxemia")},
                {'range': [90, 95], 'color': get_spo2_color("Mild Hypoxemia")},
                {'range': [95, 100], 'color': get_spo2_color("Normal")}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90 # Threshold line at 90
                }
            },
        delta = {'reference': 95, 'increasing': {'color': get_spo2_color("Normal")}, 'decreasing':{'color': get_spo2_color("Moderate Hypoxemia")}} # Delta compared to 95%
        ))
    fig.update_layout(height=250, margin={'t':50, 'b':10, 'l':10, 'r':10})
    return fig


def plot_spo2_trend(df: pd.DataFrame):
    """Plots the SpO2 trend using a line chart."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['value'],
        name='SpO2',
        mode='lines+markers',
        line=dict(color='#007bff', width=2),
        marker=dict(size=4)
    ))

    # Add threshold lines
    fig.add_hline(y=95, line_dash="dot", line_color="orange",
                  annotation_text="Normal Threshold (95%)", annotation_position="bottom right")
    fig.add_hline(y=90, line_dash="dash", line_color="red",
                  annotation_text="Alert Threshold (90%)", annotation_position="bottom right")

    fig.update_layout(
        title="Blood Oxygen (SpO2) Over Time",
        xaxis_title="Date & Time",
        yaxis_title="SpO2 (%)",
        yaxis_range=[max(70, df['value'].min() - 2), 101], # Dynamic y-axis range, min 70
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_traces(hovertemplate='<b>Time</b>: %{x|%Y-%m-%d %H:%M:%S}<br><b>SpO2</b>: %{y}%<extra></extra>')


    st.plotly_chart(fig, use_container_width=True)


def run_lowest_reading_analysis(user_id=None):
    """Calls the backend endpoint for lowest SpO2 reading check."""
    API_BASE_URL = "http://localhost:8000/api"
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    endpoint_url = f"{API_BASE_URL}/spo2/lowest_reading/"

    # Allow selecting the period for lowest reading check
    days_options = {"Last 24 hours": 1, "Last 3 days": 3, "Last 7 days": 7}
    selected_period = st.selectbox("Check lowest reading over:", list(days_options.keys()), index=1, key=f"spo2_lowest_period_{user_id or 'self'}")
    days_param = days_options[selected_period]

    params = {'days': days_param}
    if user_id:
        params['user_id'] = user_id

    with st.spinner(f"Finding lowest reading in the last {selected_period}..."):
        try:
            response = requests.get(endpoint_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            lowest_value_str = data.get('lowest_oxygen_level', 'N/A')
            # Extract numeric part if string contains '%'
            try:
                lowest_value = int(lowest_value_str.replace('%', ''))
            except (ValueError, AttributeError):
                 lowest_value = None


            if lowest_value is not None:
                st.metric(f"Lowest SpO2 ({selected_period})", f"{lowest_value}%")
                if lowest_value < 90:
                    st.error("⚠️ Lowest reading is below the critical threshold (90%).")
                elif lowest_value < 95:
                    st.warning("⚠️ Lowest reading is below the normal threshold (95%).")
                else:
                    st.success("✅ Lowest reading remained within the normal range.")
            elif lowest_value_str == 'N/A':
                 st.info(f"No SpO2 data found in the last {selected_period} to determine the lowest reading.")
            else:
                 st.info(f"Could not determine lowest reading. API response: {lowest_value_str}")


        except requests.exceptions.RequestException as e:
            st.error(f"Failed to retrieve lowest reading. Error: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")


def run_alert_check(user_id=None):
    """Calls the backend endpoint for SpO2 alert check based on the *very latest* reading."""
    API_BASE_URL ="http://localhost:8000/api"
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    endpoint_url = f"{API_BASE_URL}/spo2/alert_check/"

    params = {}
    if user_id:
        params['user_id'] = user_id

    with st.spinner("Checking latest reading for alerts..."):
        try:
            response = requests.get(endpoint_url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                message = data.get('message')
                alert_level = data.get('alert_level', 'info') 
                if alert_level == 'critical':
                     st.error(f"🚨 CRITICAL ALERT: {message}")
                elif alert_level == 'warning':
                     st.warning(f"⚠️ ALERT: {message}")
                else:
                     st.success(f"✅ OK: {message}")

            elif response.status_code == 404:
                 st.info("No recent SpO2 data found to perform alert check.")
            else:
                response.raise_for_status() 

        except requests.exceptions.RequestException as e:
            st.error(f"Failed to perform alert check. Error: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")