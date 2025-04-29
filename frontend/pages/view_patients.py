import streamlit as st
import pandas as pd
import requests
import logging
from pages import dashboard, blood_pressure, heart_rate, daily_steps, sleep_duration, spo2
from utils.api import get_user_list

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


ROLE_USER = 'USER'
ROLE_DOCTOR = 'DOCTOR'
ROLE_NURSE = 'NURSE'
ROLE_ADMIN = 'ADMIN'

ALLOWED_ROLES = [ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN]

# --- Cached Data Fetching ---
@st.cache_data(ttl=600)
def cached_get_user_list():
    """Fetches and caches the patient list from the API."""
    logging.info("CACHE MISS: Fetching user list from API")
    df = get_user_list()
    if isinstance(df, pd.DataFrame) and not df.empty:
        required_cols = ['id', 'first_name', 'last_name']
        if all(col in df.columns for col in required_cols):
            df['display_name'] = df.apply(
                lambda row: f"{row.get('last_name', 'N/A')}, {row.get('first_name', 'N/A')} (ID: {row['id']})",
                axis=1
            )
            return df
        else:
            logging.error(f"User list DataFrame missing required columns: {required_cols}")
            return pd.DataFrame()
    elif isinstance(df, pd.DataFrame) and df.empty:
        logging.info("API returned an empty user list.")
        return pd.DataFrame()
    else:
        logging.error("Failed to fetch or parse user list, API function did not return a DataFrame.")
        return None

def show_view_patients_page():
    """Displays the View Patient Data page for authorized professionals."""

    current_role = st.session_state.get("role", "USER")
    if current_role not in ALLOWED_ROLES:
        st.error("🚫 Access Denied: You do not have permission to view this page.")
        st.stop()

    st.title("View Patient Data")
    st.markdown(
            f"<h3>Logged in as {st.session_state.get("role_display", "User")} {st.session_state.get("first_name","")}</h3>",
            unsafe_allow_html=True
        )

    with st.spinner("Loading patient list..."):
        patients_df_full = cached_get_user_list()

    if patients_df_full is None:
        st.error("Error loading patient list. Could not fetch data from API.")
        st.stop()
    if patients_df_full.empty:
        st.warning("No patients found in the system or accessible to you.")


    st.markdown("---")
    search_query = st.text_input("Search Patients (by Name or ID):", key="patient_search")

    patients_df_filtered = pd.DataFrame(columns=patients_df_full.columns if patients_df_full is not None else [])
    if patients_df_full is not None and not patients_df_full.empty:
        if search_query:
            search_lower = search_query.lower()
            try:
                patients_df_filtered = patients_df_full[
                    patients_df_full['display_name'].str.lower().str.contains(search_lower)
                ]
            except Exception as e:
                st.error(f"Error during search: {e}")
                patients_df_filtered = patients_df_full
        else:
            patients_df_filtered = patients_df_full

    st.markdown("Select a patient from the list below to view their health metrics.")

    selected_patient_id = None
    if not patients_df_filtered.empty:
        patient_options = pd.Series(
            patients_df_filtered['id'].values,
            index=patients_df_filtered['display_name']
        ).to_dict()
        options_with_placeholder = {"-- Select a Patient --": None}
        options_with_placeholder.update(patient_options)

        selected_display_name = st.selectbox(
            "Select Patient:",
            options=list(options_with_placeholder.keys()),
            index=0,
            key="patient_selector"
        )
        selected_patient_id = options_with_placeholder[selected_display_name]

    elif patients_df_full is None or patients_df_full.empty:
         st.info("There are no patients available to display.")
    else: # Filtered list is empty, but full list was not
        st.info(f"No patients found matching your search query: '{search_query}'")

    if selected_patient_id:
        st.divider()
        # Get details from the *original* full DataFrame
        patient_details = patients_df_full[patients_df_full['id'] == selected_patient_id].iloc[0]
        first_name = patient_details.get('first_name', 'N/A')
        last_name = patient_details.get('last_name', 'N/A')
        age = patient_details.get('age', 'N/A')
        gender = patient_details.get('gender', 'N/A')

        # Display Patient Demographics
        st.subheader(f"Viewing Data for: {last_name}, {first_name}")
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1: st.write(f"**Patient ID:** {selected_patient_id}")
        with col_info2: st.write(f"**Age:** {age}")
        with col_info3: st.write(f"**Gender:** {gender}")
        st.divider()

        all_metric_pages = {
            "Dashboard Summary": (dashboard.show_dashboard, [ROLE_USER, ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN]),
            "Heart Rate": (heart_rate.show_heart_rate_page, [ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN]),
            "Blood Pressure": (blood_pressure.show_blood_pressure_page, [ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN]),
            "Daily Steps": (daily_steps.show_daily_steps_page, [ROLE_USER, ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN]),
            "Sleep Duration": (sleep_duration.show_sleep_duration_page, [ROLE_USER, ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN]),
            "SpO2 (Blood Oxygen)": (spo2.show_spo2_page, [ROLE_USER, ROLE_DOCTOR, ROLE_NURSE, ROLE_ADMIN]),
        }

        available_metrics = {
            name: func_role_tuple[0]
            for name, func_role_tuple in all_metric_pages.items()
            if current_role in func_role_tuple[1]
        }

        tab_labels = list(available_metrics.keys())

        if not tab_labels:
            st.warning("No metrics available for your role to display for this patient.")
            st.stop()

        st.markdown("#### Select Metric to View")

        created_tabs = st.tabs(tab_labels)

        for i, tab_container in enumerate(created_tabs):
            tab_label = tab_labels[i]
            with tab_container:
                page_function_to_call = available_metrics.get(tab_label)

                if page_function_to_call:
                    try:
                        logging.info(f"Rendering active tab '{tab_label}' for user {selected_patient_id}")
                        page_function_to_call(user_id=selected_patient_id)
                    except Exception as e:
                        st.error(f"An error occurred while loading the '{tab_label}' tab for Patient ID {selected_patient_id}:")
                        st.exception(e)
                else:
                    st.error(f"Internal Error: Could not find function mapping for tab '{tab_label}'.")

    elif patients_df_full is not None and not patients_df_full.empty and not search_query:
        st.info("Please select a patient from the dropdown above to view their details.")