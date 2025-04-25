import streamlit as st
from utils.api import get_blood_pressure_data
import plotly.graph_objects as go
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import datetime
import requests
import time


# Auto-refresh every 5 seconds
refresh_interval = 5 * 1000  # milliseconds
st_autorefresh(interval=refresh_interval, key="bp_autorefresh")

def show_blood_pressure_page():
    st.title("Blood Pressure Monitoring")

    col1, col2 = st.columns([3, 1])
    with col1:
        time_period = st.selectbox(
            "Select time period:",
            ["Last 24 hours", "Last 7 days", "Last 30 days", "Custom range"]
        )

    with col2:
        refresh_button = st.button("Refresh data")

    # Handle custom date range
    if time_period == "Custom_range":
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start date", datetime.datetime.now() - datetime.timedelta(days=7))
        with col2:
            end_date = st.date_input("End date", datetime.datetime.now())
        days = (end_date - start_date) + 1
    else:
        days = {"Last 24 hours": 1, "Last 7 days": 7, "Last 30 days": 30}[time_period]

    if refresh_button:
        with st.spinner("Refreshing data..."):
            time.sleep(0.5)

    blood_pressure_df = get_blood_pressure_data(days)

    if blood_pressure_df.empty:
        st.warning("No blood pressure data available for the selected period. Please check your connection or try another time range.")
        st.stop()

    # Display summary metrics
    st.subheader("Blood Pressure Summary")

    col1, col2, col3 = st.columns(3)

    with col1:
        latest_reading = blood_pressure_df.iloc[-1]
        latest_systolic = latest_reading['systolic']
        latest_diastolic = latest_reading['diastolic']
        st.metric("Latest Reading", f"{latest_systolic}/{latest_diastolic} mmHg")
        
        category = get_bp_category(latest_systolic, latest_diastolic)
        color = get_category_color(category)
        
        st.metric(
            "Latest Reading",
            f"{latest_systolic}/{latest_diastolic} mmHg",
            delta=None
        )
        st.markdown(
            f"<h3 style='color:{color}; font-weight:bold; font-size:28px; margin-top:10px;'>{category}</h3>",
            unsafe_allow_html=True
)

    with col2:
        avg_systolic = blood_pressure_df['systolic'].mean()
        avg_diastolic = blood_pressure_df['diastolic'].mean()
        st.metric(
            "Average",
            f"{avg_systolic:.1f}/{avg_diastolic:.1f} mmHg"
        )
        reading_count = len(blood_pressure_df)
        st.caption(f"Based on {reading_count} readings")

    with col3:
        min_systolic, max_systolic = blood_pressure_df['systolic'].min(), blood_pressure_df['systolic'].max()
        min_diastolic, max_diastolic = blood_pressure_df['diastolic'].min(), blood_pressure_df['diastolic'].max()

        st.metric("Range (Systolic)", f"{min_systolic:.0f} - {max_systolic:.0f} mmHg")
        st.metric("Range (Diastolic)", f"{min_diastolic:.0f} - {max_diastolic:.0f} mmHg")

    # Blood Pressure Chart
    st.subheader("Blood Pressure Chart")
    plot_blood_pressure_trend(blood_pressure_df)

    # Time of Day Analysis
    if "access_token" in st.session_state and len(blood_pressure_df) > 3:
        st.subheader("Time of Day Analysis")
        run_time_of_day_analysis()

    if "access_token" in st.session_state and len(blood_pressure_df) > 0:
        st.subheader("Age Based-Assessment")
        run_age_comparison()

    if "access_token" in st.session_state and len(blood_pressure_df) > 3:
        st.subheader("Blood Pressure Elevation Check")
        run_elevation_check()


def plot_blood_pressure_trend(df):
    # Create line chart for BP trend
    fig = go.Figure()
    
    # Add systolic trace with shaded regions
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['systolic'],
        name='Systolic',
        line=dict(color='#F63366', width=2),
        mode='lines+markers'
    ))
    
    # Add diastolic trace
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['diastolic'],
        name='Diastolic',
        line=dict(color='#0068C9', width=2),
        mode='lines+markers'
    ))
    
    # Add reference lines for normal ranges
    fig.add_shape(
        type="line",
        x0=df['timestamp'].min(),
        x1=df['timestamp'].max(),
        y0=120,
        y1=120,
        line=dict(color="rgba(246, 51, 102, 0.5)", width=1, dash="dash"),
    )
    
    fig.add_shape(
        type="line",
        x0=df['timestamp'].min(),
        x1=df['timestamp'].max(),
        y0=80,
        y1=80,
        line=dict(color="rgba(0, 104, 201, 0.5)", width=1, dash="dash"),
    )
    
    # Add annotations for the reference lines
    fig.add_annotation(
        x=df['timestamp'].max(),
        y=120,
        text="Normal Systolic",
        showarrow=False,
        yshift=10,
        xshift=-5,
        align="right",
        font=dict(size=10, color="rgba(246, 51, 102, 0.8)")
    )
    
    fig.add_annotation(
        x=df['timestamp'].max(),
        y=80,
        text="Normal Diastolic",
        showarrow=False,
        yshift=-15,
        xshift=-5,
        align="right",
        font=dict(size=10, color="rgba(0, 104, 201, 0.8)")
    )
    
    # Update layout
    fig.update_layout(
        title="Blood Pressure Readings Over Time",
        xaxis_title="Date & Time",
        yaxis_title="Blood Pressure (mmHg)",
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
    
    st.plotly_chart(fig, use_container_width=True)

        


def run_time_of_day_analysis():
    # Display time of day analysis from custom endpoint
    API_BASE_URL = "http://localhost:8000/api/"
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}

    col1, col2 = st.columns([4, 1])

    with col2:
        days = st.selectbox("Analysis period", [1, 3, 7, 14, 30, 60, 90], index=1)

    with st.spinner("Analyzing time of day patterns"):
        response = requests.get(
            f"{API_BASE_URL}/blood-pressure/time_of_day_analysis/?days={days}",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()

            # Create columns for morning and evening
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Morning Averages")
                morning = data.get('morning_averages', {})
                if morning:
                    st.metric("Systolic", f"{morning.get('avg_systolic' , 'N/A'):.1f}")
                    st.metric("Diastolic", f"{morning.get('avg_diastolic', 'N/A'):.1f}")
                    st.caption(f"Based on {data.get('reading_count', 0)} readings")
                else:
                    st.info("No morning data available")
                
            with col2:
                st.subheader("Evening Averages")
                evening = data.get('evening_averages', {})
                if evening:
                    st.metric("Systolic", f"{evening.get('avg_systolic' , 'N/A'):.1f}")
                    st.metric("Diastolic", f"{evening.get('avg_diastolic', 'N/A'):.1f}")
                    st.caption(f"Based on {data.get('reading_count', 0)} readings")
                else:
                    st.info("No evening data available")

            # Display pattern information if available
            pattern = data.get('pattern', {})
            if pattern:
                pattern_type = pattern.get('type', 'Unknown')
                description = pattern.get('description', '')
                sys_diff = pattern.get('systolic_difference', 0)

                st.info(f"**Pattern Analysis:** {description} (Systolic difference: {sys_diff} mmHg)")
        else:
            st.error("Failed to retrieve any time of day analysis")
            
def run_age_comparison():
    # Display age comparison from custom endpoint
    API_BASE_URL = "http://localhost:8000/api"
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}

    # Get user age from session if available, otherwise use input
    age = None
    if "age" in st.session_state and st.session_state["age"]:
        age = st.session_state["age"]

    if not age or not isinstance(age, int):
        age = st.number_input("Enter user age for personalized assessment", min_value=18, max_value=120, value=40, format='%d')

    with st.spinner("Generating age-based assessment"):
        response = requests.get(
            f"{API_BASE_URL}/blood-pressure/age_comparison?age={age}",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()

            # Extract data
            latest_reading = data.get('latest_reading', {})
            age_assessment = data.get('age_specific_assessment', {})
            recommendation = data.get('recommendation', '')

            # Format data
            systolic = latest_reading.get('systolic', 'N/A')
            diastolic = latest_reading.get('diastolic', 'N/A')
            category = latest_reading.get('category', 'Unknown')
            within_range = age_assessment.get('within_recommended_range', False)

            # Display visual indicator
            if within_range:
                st.success(f"✅ Your blood pressure ({systolic}/{diastolic} mmHg) is within the recommended range for your age.")
            else:
                st.warning(f"⚠️ Your blood pressure ({systolic}/{diastolic} mmHg) may need attention based on your age.")

            # Show recommendation
            if recommendation:
                st.info(recommendation)

            # Show recommended ranges
            st.subheader("Age-Specific Recommended Ranges")
            ranges = age_assessment.get('recommended_ranges', {})
            st.write(f"- Systolic: {ranges.get('systolic', 'N/A')}")
            st.write(f"- Diastolic: {ranges.get('diastolic', 'N/A')}")
        else:
            st.error("Failed to retrieve age-based comparison")

def run_elevation_check():
    # Check if blood pressure is consistently elevated
    API_BASE_URL = "http://localhost:8000/api"
    headers = {"Authorization": f"Bearer {st.session_state['access_token']}"}
    col1, col2 = st.columns([4, 1])
    with col2:
        days = st.selectbox("Check period", [1,3, 7, 14, 30], index=1, key="elevation_days")
    
    with st.spinner("Checking blood pressure elevation..."):
        response = requests.get(
            f"{API_BASE_URL}/blood-pressure/elevation_check/?days={days}",
            headers=headers
        )
    
        if response.status_code == 200:
            data = response.json()
            is_elevated = data.get('is_consistently_elevated', False)
            days_checked = data.get('days_checked', days)
            
            if is_elevated:
                st.warning(f"⚠️ Your blood pressure has been consistently elevated over the past {days_checked} days.")
                st.write("Consider consulting with a healthcare provider if this trend continues.")
            else:
                st.success(f"✅ Your blood pressure has not been consistently elevated over the past {days_checked} days.")
        else:
            st.error("Failed to retrieve elevation check data")

def get_bp_category(systolic, diastolic):
    if systolic < 120 and diastolic < 80:
        return "Normal"
    elif 120 <= systolic < 130 and diastolic < 80:
        return "Elevated"
    elif 130 <= systolic < 140 or 80 <= diastolic < 90:
        return "Stage 1 Hypertension"
    elif systolic >= 140 or diastolic >= 90:
        return "Stage 2 Hypertension"
    elif systolic >= 180 or diastolic >= 120:
        return "Hypertensive Crisis"
    else:
        return "Unknown"

def get_category_color(category):
    colors = {
        "Normal": "#4CAF50",  # Green
        "Elevated": "#FFC107",  # Yellow
        "Stage 1 Hypertension": "#FF9800",  # Orange
        "Stage 2 Hypertension": "#F44336",  # Red
        "Hypertensive Crisis": "#B71C1C",  # Dark Red
        "Unknown": "#9E9E9E"   # Grey
    }
    return colors.get(category, "#9E9E9E")