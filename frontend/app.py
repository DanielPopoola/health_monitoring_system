import streamlit as st

st.set_page_config(page_title="Health Monitoring System",
                       layout="wide", initial_sidebar_state="auto")
    
from utils.auth import logout_user
from pages import register, login, dashboard, blood_pressure, heart_rate, daily_steps, sleep_duration, spo2

ROLE_USER = 'USER'
ROLE_DOCTOR = 'DOCTOR'
ROLE_NURSE = 'NURSE'
ROLE_ADMIN = 'ADMIN'

USER_PAGES = {
    "Dashboard": dashboard.show_dashboard,
    "Daily Steps": daily_steps,
    "Sleep Duration": sleep_duration,
    "SpO2": spo2,
    "Register": register.show_register_page,
}

PROFESSIONAL_PAGES = {
    **USER_PAGES,
    "Heart Rate": heart_rate.show_heart_rate_page,
    "Blood Pressure": blood_pressure.show_blood_pressure_page,
}

ADMIN_PAGES = {
    **PROFESSIONAL_PAGES
}

def main():
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
        st.session_state.role = ROLE_USER

    if not st.session_state.is_authenticated:
        login.show_login_page()
    else:
        role = st.session_state.get("role", ROLE_USER)
        user_name = st.session_state.get("first_name", "User")
        role_display = st.session_state.get("role_display", "User")

        st.sidebar.success(f"Logged in as {user_name} ({role_display})")

        # Determine accessible pages
        if role == ROLE_USER:
            available_pages = USER_PAGES
        elif role in [ROLE_DOCTOR, ROLE_NURSE]:
            available_pages = PROFESSIONAL_PAGES
        elif role == ROLE_ADMIN:
            available_pages = ADMIN_PAGES
        else:
            available_pages  = USER_PAGES

        st.sidebar.title("Navigation")
        selection = st.sidebar.radio("Go to", list(available_pages.keys()))

        # Render selected pages
        page_function = available_pages[selection]
        page_function()

        if st.sidebar.button("Logout"):
            logout_user()
            st.rerun()

if __name__ == "__main__":
    main()