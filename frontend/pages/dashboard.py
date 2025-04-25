import streamlit as st
from utils.api import get_heart_rate_data, get_blood_pressure_data, get_spo2_data
from utils.visualizations import plot_heart_rate, plot_blood_pressure, plot_spo2_gauge


def show_dashboard():
    st.title(f"Welcome to your Health Dashboard, {st.session_state.get('first_name', 'User')}")

    time_period = st.selectbox(
        "Select time period:", 
        ["Last 24 hours", "Last 7 days", "Last 30 days"],
        index=0
    )
    
    days = {"Last 24 hours": 1, "Last 7 days": 7, "Last 30 days": 30}[time_period]
        
    # Get data
    heart_rate_df = get_heart_rate_data(days)
    blood_pressure_df = get_blood_pressure_data(days)
    spo2_df =  get_spo2_data(days)

    # Display top metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        if not heart_rate_df.empty:
            avg_hr = heart_rate_df['value'].mean()
            st.metric("Average Heart Rate", f"{avg_hr:.1f} BPM")

    with col2:
        if not blood_pressure_df.empty:
            latest_reading = blood_pressure_df.iloc[-1]
            latest_systolic = latest_reading['systolic']
            latest_diastolic = latest_reading['diastolic']
            st.metric("Current Blood Pressure", f"{latest_systolic}/{latest_diastolic} mmHg")

    with col3:
        if not spo2_df.empty:
            latest_spo2 = spo2_df.iloc[-1]['value']
            st.metric("Latest SpO₂", f"{latest_spo2:.0f}%")

    # Display charts
    st.subheader("Heart Rate")
    plot_heart_rate(heart_rate_df)
    
    st.subheader("Blood Pressure")
    plot_blood_pressure(blood_pressure_df)

    st.subheader("Oxygen Saturation (SpO2)")
    plot_spo2_gauge(spo2_df)