import streamlit as st
import pandas as pd
import logging
import requests
from utils.api import get_user_list
from pages import dashboard, blood_pressure, heart_rate, daily_steps, sleep_duration, spo2


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ROLE_USER = 'USER'
ROLE_DOCTOR = 'DOCTOR'
ROLE_NURSE = 'NURSE'
ROLE_ADMIN = 'ADMIN'

ALLOWED_ROLES = [ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN]

@st.cache_data(ttl=600)
def cached_get_user_list():
    print("CACHE MISS: Fetching user list from API")
    return get_user_list()

def show_view_patients_page():
    current_role = st.session_state.get("role", "USER")
    if current_role not in ALLOWED_ROLES:
        st.error("🚫 Access Denied: You do not have permission to view this page.")
        st.stop()
    
    st.title("View Patient Data")
    st.write(f"Logged in as {st.session_state.get('first_name', '')} ({st.session_state.get('role_display', '')})")
    st.markdown("Select a patient from the list below to view their health metrics.")

    with st.spinner("Loading patient list..."):
        patients_df = cached_get_user_list()

    if patients_df is None or patients_df.empty:
        st.error("Could not load patient list. Please check the API connection or ensure patients exist.")
        st.stop()

    patients_df['display_name'] = patients_df.apply(
        lambda row: f"{row.get('last_name', 'N/A')}, {row.get('first_name', 'N/A')} (ID: {row['id']})",
        axis=1
    )

    patient_options = pd.Series(patients_df['id'].values, index=patients_df['display_name']).to_dict()
    options_with_placeholder = {"-- Select a Patient --": None}
    options_with_placeholder.update(patient_options)

    selected_display_name = st.selectbox(
        "Select Patient:",
        options=list(options_with_placeholder.keys()),
        index=0,
        key='patient_selector'
    )

    selected_patient_id = options_with_placeholder[selected_display_name]

    # --- Display Patient Data ---
    if selected_patient_id:
        st.divider()
        patient_details = patients_df[patients_df['id'] == selected_patient_id].iloc[0]
        first_name = patient_details.get('first_name', 'N/A')
        last_name = patient_details.get('last_name', 'N/A')
        age = patient_details.get('age', 'N/A')
        gender = patient_details.get('gender', 'N/A')

        st.subheader(f"Viewing Data for: {last_name}, {first_name}")
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1: st.write(f"**Patient ID:** {selected_patient_id}")
        with col_info2: st.write(f"**Age:** {age}")
        with col_info3: st.write(f"**Gender:** {gender}")

        st.divider()

        all_metric_pages = {
            "Dashboard Summary": (dashboard.show_dashboard, [ROLE_USER, ROLE_NURSE, ROLE_ADMIN]),
            "Heart Rate": (heart_rate.show_heart_rate_page, [ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN]),
            "Blood Pressure": (blood_pressure.show_blood_pressure_page, [ROLE_DOCTOR, ROLE_ADMIN]),
            "Daily Steps": (daily_steps.show_daily_steps_page, [ROLE_USER, ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN]),
            "Sleep Duration": (sleep_duration.show_sleep_duration_page, [ROLE_USER, ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN]),
            "SpO2 (Blood Oxygen)": (spo2.show_spo2_page, [ROLE_USER, ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN]),
        }

        # Filter available metrics based on the logged-in professional's role
        available_metrics = {
            name: func_role_tuple[0] # Get only the function
            for name, func_role_tuple in all_metric_pages.items()
            if current_role in func_role_tuple[1] # Check if current role is allowed
        }

        tab_labels = list(available_metrics.keys())

        if not tab_labels:
            st.warning("No metrics available for your role to display.")
            st.stop()

        st.markdown("#### Select Metric to View")

        # --- Create Tabs & Get Selected Tab ---
        # This returns the LABEL of the selected tab
        selected_tab_label = st.tabs(tab_labels)

        page_function_to_call = available_metrics.get(selected_tab_label)

        if page_function_to_call:
            try:
                logging.info(f"Calling function for active tab '{selected_tab_label}' for user {selected_patient_id}")
                page_function_to_call(user_id=selected_patient_id)
            except Exception as e:
                st.error(f"An error occurred while loading the '{selected_tab_label}' tab for Patient ID {selected_patient_id}:")
                st.exception(e)
        else:
            st.error(f"Internal error: Could not find the function associated with the selected tab '{selected_tab_label}'.")
    else:
        st.info("Please select a patient from the dropdown above to view their details.")