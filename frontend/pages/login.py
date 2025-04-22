import streamlit as st
from utils.auth import login_user

def show_login_page():
    st.title("Login to Health Monitoring System")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        submit_button = st.form_submit_button("Login")

        if submit_button:
            if not email or not password:
                st.error("Invalid credentials")
            else:
                success, message = login_user(email, password)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

    st.markdown("Don't have an account? [Register here](/Register)")