import streamlit as st
from utils.api import (
    get_heart_rate_data, 
    get_blood_pressure_data,
    get_spo2_data,
    get_daily_steps_data)
from utils.visualizations import (
    plot_heart_rate, 
    plot_blood_pressure, 
    plot_spo2_gauge,
    plot_daily_steps)

def show_dashboard():
    st.title(f"Welcome to your Health Dashboard, {st.session_state.get('first_name', 'User')}")

    time_period = st.selectbox(
        "Select time period:", 
        ["Last 1 hour", "Last 6 hours", "Last 12 hours","Last 24 hours", "Last 7 days", "Last 30 days"],
        index=0
    )
    
    if time_period == "Last 1 hour":
        hr_days, hr_hours = 0, 1
        other_days = 1
    elif time_period == "Last 6 hours":
        hr_days, hr_hours = 0, 6
        other_days = 1
    elif time_period == "Last 12 hours":
        hr_days, hr_hours = 0, 12
        other_days = 1
    elif time_period == "Last 24 hours":
        hr_days, hr_hours = 0, 24
        other_days = 1
    elif time_period == "Last 7 days":
        hr_days, hr_hours = 7, 0
        other_days = 7
    else:  # Last 30 days
        hr_days, hr_hours = 30, 0
        other_days = 30
    
        
    # Get data
    heart_rate_df = get_heart_rate_data(days=hr_days, hours=hr_hours)
    blood_pressure_df = get_blood_pressure_data(other_days)
    spo2_df =  get_spo2_data(other_days)
    daily_steps_df = get_daily_steps_data(other_days)

    # Display top metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if not heart_rate_df.empty:
            avg_hr = heart_rate_df['value'].mean()
            st.metric("Average Heart Rate", f"{avg_hr:.1f} BPM")

    with col2:
        if not blood_pressure_df.empty:
            latest_reading = blood_pressure_df.iloc[-1]
            latest_systolic = latest_reading['systolic']
            latest_diastolic = latest_reading['diastolic']
            st.metric("Latest Reading", f"{latest_systolic}/{latest_diastolic} mmHg")

    with col3:
        if not spo2_df.empty:
            latest_spo2 = spo2_df.iloc[-1]['value']
            st.metric("Latest SpO₂", f"{latest_spo2:.0f}%")

    with col4:
        if not daily_steps_df.empty:
            latest_entry = daily_steps_df.iloc[-1]
            latest_steps = latest_entry['count']
            latest_goal = latest_entry.get('goal', 10000)
            latest_date = latest_entry['timestamp']
            st.metric("Latest Steps", f"{latest_steps:,}", help=f"Recorded on {latest_date}")
            st.metric("Goal", f"{latest_goal}")


    # Display charts
    st.subheader("Heart Rate")
    plot_heart_rate(heart_rate_df)
    
    st.subheader("Blood Pressure")
    plot_blood_pressure(blood_pressure_df)

    st.subheader("Oxygen Saturation (SpO2)")
    plot_spo2_gauge(spo2_df)

    st.subheader("Daily Steps")
    plot_daily_steps(daily_steps_df)