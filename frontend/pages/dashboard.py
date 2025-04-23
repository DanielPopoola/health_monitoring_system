import streamlit as st
from utils.api import get_heart_rate_data, get_blood_pressure_data, get_spo2_data
from utils.visualizations import plot_heart_rate, plot_blood_pressure

def show_dashboard():
    st.title(f"Welcome to your Health Dashboard, {st.session_state.get('first_name', 'User')}")

    time_period = st.selectbox(
        "Select time period:",
        ["Last 24 hours", "Last 7 days", "Last 30 days"],
        index=0
    )

    days = 1
    if time_period == "Last 7 days":
        days = 7
    elif time_period == "Last 30 days":
        days = 30

    # Get data
    heart_rate_df = get_heart_rate_data(days)
    blood_pressure_df = get_blood_pressure_data(days)

    # Display metrics
    col1, col2 = st.columns(2)

    with col1:
        if not heart_rate_df.empty:
            latest_hr = heart_rate_df.iloc[-1]['value']
            st.metric("Latest Heart Rate", f"{latest_hr} BPM")

    with col2:
        if not blood_pressure_df.empty:
            latest_bp = blood_pressure_df.iloc[-1]
            st.metric("Latest Blood Pressure", f"{latest_bp['systolic']}/{latest_bp['diastolic']} mmHg")

    # Display charts
    st.subheader("Heart Rate")
    plot_heart_rate(heart_rate_df)
    
    st.subheader("Blood Pressure")
    plot_blood_pressure(blood_pressure_df)