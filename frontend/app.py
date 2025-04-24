import streamlit as st
from pages.login import show_login_page
from pages.register import show_register_page
from pages.dashboard import show_dashboard
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

with st.sidebar:
    show_sidebar = st.checkbox("Toggle Sidebar", value=True)

if show_sidebar:
    with st.sidebar:
        st.title("Health Monitoring")

        if st.session_state.get("is_authenticated", False):
            st.write(f"Logged in as: {st.session_state.get('first_name', 'User')}")
            if st.button("Logout"):
                logout_user()
                st.rerun()
        else:
            page = st.radio("Navigation", ["Login", "Register"])

if st.session_state.get("is_authenticated", False):
    show_dashboard()
else:
    if page == "Login":
        show_login_page()
    else:
        show_register_page()
