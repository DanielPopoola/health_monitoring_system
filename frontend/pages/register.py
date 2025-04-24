import streamlit as st
from utils.auth import register_user

def show_register_page():
    st.title("Register for Health Monitoring System")

    with st.form("register_form"):
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        age = st.number_input("Age", step=1, format="%d")
        gender= st.text_input("Gender")
        #name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type='password')

        submit_button = st.form_submit_button("Register")

        if submit_button:
            if password != confirm_password:
                st.error("Passwords do not match!")
            elif not first_name or not last_name or not age or not gender or not email or not password:
                st.error("All fields required!")
            else:
                success, message = register_user(
                    first_name=first_name,
                    last_name=last_name,
                    age=age,
                    name=f"{first_name} {last_name}",
                    gender=gender,
                    email=email,
                    password=password
                )
                if success:
                    st.success(message)
                    st.info("Please head to the login page to sign in")
                else:
                    st.error(message)
