import streamlit as st
from pages.login import show_login_page
from pages.register import show_register_page
from pages.dashboard import show_dashboard
from pages.blood_pressure import show_blood_pressure_page
from utils.auth import logout_user

# Set page config
st.set_page_config(
    page_title="Health Monitoring System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "is_authenticated" not in st.session_state:
    st.session_state["is_authenticated"] = False

# Set a default for the page
if "page" not in st.session_state:
    st.session_state["page"] = "Login"

# Sidebar toggle
with st.sidebar:
    show_sidebar = st.checkbox("Toggle Sidebar", value=True)

if show_sidebar:
    with st.sidebar:
        st.title("Health Monitoring")

        if st.session_state.get("is_authenticated", False):
            st.write(f"Logged in as: {st.session_state.get('first_name', 'User')}")
            selected_page = st.radio("Navigation", ["Dashboard", "Blood Pressure", "Logout"])

            if selected_page == "Logout":
                logout_user()
                st.session_state["page"] = "Login"
                st.rerun()
            else:
                st.session_state["page"] = selected_page

        else:
            selected_page = st.radio("Navigation", ["Login", "Register", "Blood Pressure"])
            st.session_state["page"] = selected_page

# Render the appropriate page
if st.session_state["page"] == "Dashboard" and st.session_state.get("is_authenticated", False):
    show_dashboard()
elif st.session_state["page"] == "Blood Pressure" and st.session_state.get("is_authenticated", False):
    show_blood_pressure_page()
elif st.session_state["page"] == "Login":
    show_login_page()
elif st.session_state["page"] == "Register":
    show_register_page()

