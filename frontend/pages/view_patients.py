import streamlit as st
import pandas as pd
import requests
from utils.api import get_user_list
from pages import dashboard, blood_pressure, heart_rate, daily_steps, sleep_duration, spo2 
ALLOWED_ROLES = ['DOCTOR', 'NURSE', 'ADMIN']

ROLE_USER = 'USER'
ROLE_DOCTOR = 'DOCTOR'
ROLE_NURSE = 'NURSE'
ROLE_ADMIN = 'ADMIN'

@st.cache_data(ttl=600) # Cache for 10 minutes
def cached_get_user_list():
    print("CACHE MISS: Fetching user list from API")
    return get_user_list()

def show_view_patients_page():
    current_role = st.session_state.get("role", "USER")
    if current_role not in ALLOWED_ROLES:
        st.error("🚫 Access Denied: You do not have permission to view this page.")
        st.stop()

    st.title("View Patient Data")
    st.write(f"Logged in as ({st.session_state.get('role_display', '')}) {st.session_state.get('first_name', '')} ")
    st.markdown("Select a patient from the list below to view their health metrics.")

    # --- Patient Selection ---
    with st.spinner("Loading patient list..."):
        patients_df = cached_get_user_list()

    if patients_df is None or patients_df.empty:
        st.error("Could not load patient list. Please check the API connection or ensure patients exist.")
        st.stop()

    # Create display names (e.g., "Last, First (ID: 1)")
    patients_df['display_name'] = patients_df.apply(
        lambda row: f"{row.get('last_name', '')}, {row.get('first_name', '')} (ID: {row['id']})",
        axis=1
    )
    patient_options = pd.Series(patients_df['id'].values, index=patients_df['display_name']).to_dict()
    # Add a placeholder option
    options_with_placeholder = {"-- Select a Patient --": None}
    options_with_placeholder.update(patient_options)


    selected_display_name = st.selectbox(
        "Select Patient:",
        options=list(options_with_placeholder.keys()),
        index=0 # Default to placeholder
    )

    selected_patient_id = options_with_placeholder[selected_display_name]

    # Store selected patient ID in session state for potential use across refreshes or pages
    st.session_state.selected_patient_id = selected_patient_id

    # --- Display Patient Data ---
    if selected_patient_id:
        st.divider()
        # Find selected patient's details from the dataframe
        patient_details = patients_df[patients_df['id'] == selected_patient_id].iloc[0]
        first_name = patient_details.get('first_name', 'N/A')
        last_name = patient_details.get('last_name', 'N/A')
        age = patient_details.get('age', 'N/A')
        gender = patient_details.get('gender', 'N/A')
        email = patient_details.get('email', 'N/A')

        st.subheader(f"Viewing Data for: {last_name}, {first_name}")
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.write(f"**Patient ID:** {selected_patient_id}")
        with col_info2:
            st.write(f"**Age:** {age}")
        with col_info3:
            st.write(f"**Gender:** {gender}")

        st.divider()

        # --- Metric Selection for the Chosen Patient ---
        st.markdown("#### Select Metric to View")

        # Define which pages/functions to call, passing the user_id
        # Mapping display name to the function and potentially required roles
        metric_pages = {
            "Dashboard Summary": (dashboard.show_dashboard, [ROLE_USER, ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN]),
            "Heart Rate": (heart_rate.show_heart_rate_page, [ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN]),
            "Blood Pressure": (blood_pressure.show_blood_pressure_page, [ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN]),
            "Daily Steps": (daily_steps.show_daily_steps_page, [ROLE_USER, ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN]),
            "Sleep Duration": (sleep_duration.show_sleep_duration_page, [ROLE_USER, ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN]),
            "SpO2 (Blood Oxygen)": (spo2.show_spo2_page, [ROLE_USER, ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN]), 
        }

        # Filter available metrics based on the *logged-in professional's* role
        available_metrics = {
            name: func_role_tuple[0]
            for name, func_role_tuple in metric_pages.items()
            if current_role in func_role_tuple[1]
        }
        print(available_metrics)


        metric_tabs = st.tabs(list(available_metrics.keys()))

        for i, tab_name in enumerate(available_metrics.keys()):
            with metric_tabs[i]:
                page_function = available_metrics[tab_name]
                try:
                    # Call the specific page's function, passing the selected patient ID
                    st.write(f"--- Displaying {tab_name} for Patient ID: {selected_patient_id} ---")
                    page_function(user_id=selected_patient_id)
                except Exception as e:
                    st.error(f"Error loading {tab_name} for Patient ID {selected_patient_id}: {e}")
                    st.exception(e) # Show traceback for debugging

    else:
        st.info("Please select a patient from the dropdown above to view their details.")