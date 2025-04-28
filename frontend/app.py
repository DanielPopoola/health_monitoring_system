# hm app.py (Updated Snippet)

import streamlit as st

st.set_page_config(page_title="Health Monitoring System",
                       layout="wide", initial_sidebar_state="auto")

from utils.auth import logout_user
# Import page modules
from pages import register, login, dashboard, blood_pressure, heart_rate, daily_steps, sleep_duration, spo2, view_patients
ROLE_USER = 'USER'
ROLE_DOCTOR = 'DOCTOR'
ROLE_NURSE = 'NURSE'
ROLE_ADMIN = 'ADMIN'

# Define pages accessible by ROLE_USER
USER_PAGES = {
    "Dashboard": dashboard.show_dashboard,
    "Daily Steps": daily_steps.show_daily_steps_page,      
    "Sleep Duration": sleep_duration.show_sleep_duration_page, 
    "SpO2": spo2.show_spo2_page,                     
    "Register": register.show_register_page,
}

# Define pages accessible by professional roles (inherits USER_PAGES)
PROFESSIONAL_PAGES = {
    **USER_PAGES,
    "Heart Rate": heart_rate.show_heart_rate_page,
    "Blood Pressure": blood_pressure.show_blood_pressure_page,
    "View Patients": view_patients.show_view_patients_page, 
}

# Define pages accessible by admin (inherits PROFESSIONAL_PAGES)
ADMIN_PAGES = {
    **PROFESSIONAL_PAGES
}

def main():
    # Initialize session state if not already done
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
        st.session_state.role = None 
        st.session_state.first_name = None
        st.session_state.role_display = None
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.email = None
        st.session_state.age = None

    if not st.session_state.is_authenticated:
        login.show_login_page()
        if st.query_params.get("page") == "register":
             register.show_register_page()

    else:
        role = st.session_state.get("role", ROLE_USER) 
        user_name = st.session_state.get("first_name", "User")
        role_display = st.session_state.get("role_display", "User Role")

        st.sidebar.success(f"Logged in as {user_name} ({role_display})")

        # Determine accessible pages based on role
        if role == ROLE_USER:
            available_pages = USER_PAGES
        elif role in [ROLE_DOCTOR, ROLE_NURSE]:
            available_pages = PROFESSIONAL_PAGES
        elif role == ROLE_ADMIN:
            available_pages = ADMIN_PAGES
        else:
            # Fallback for unknown roles or if role is None
            st.warning("Unknown user role assigned. Displaying default pages.")
            available_pages = USER_PAGES

        # Remove 'Register' if logged in
        available_pages.pop("Register", None)

        st.sidebar.title("Navigation")

        # Check if a specific page is requested via query param (useful for direct links)
        query_page = st.query_params.get("page")
        page_keys = list(available_pages.keys())
        default_selection_index = 0
        if query_page and query_page in page_keys:
            default_selection_index = page_keys.index(query_page)


        selection = st.sidebar.radio(
            "Go to",
            page_keys,
            index=default_selection_index,
            key="navigation_radio"
            )
        
        st.query_params["page"] = selection

        if selection != "View Patients" and "selected_patient_id" in st.session_state:
             st.session_state.selected_patient_id = None

        page_function = available_pages[selection]

        page_function()

        if st.sidebar.button("Logout"):
            logout_user()
            st.query_params.clear()
            st.rerun()

if __name__ == "__main__":
    main()