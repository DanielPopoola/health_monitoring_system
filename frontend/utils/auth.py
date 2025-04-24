import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000/api"

def register_user(email, password, first_name: str, last_name: str, name: str, age: int, gender: str):
    user_data ={
            "email": email,
            "password": password,
            "first_name": first_name,
            "last_name": last_name,
            "name": name,
            "age":age,
            "gender": gender}
    print(user_data)
    response = requests.post(
        f"{API_BASE_URL}/register",json=user_data)
    try:
        if response.status_code == 201:
            return True, "Registration successful!"
    except requests.exceptions.JSONDecodeError:
        return False, f"Invalid response: {response.status_code} - {response.text}"

def login_user(email, password):
    response = requests.post(
        f"{API_BASE_URL}/token/",
        json={"email": email, "password": password}
    )
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access"]
        refresh_token = token_data["refresh"]
        # Store tokens in session state
        st.session_state["access_token"] = access_token
        st.session_state["refresh_token"] = refresh_token
        st.session_state["email"] = email
        st.session_state["is_authenticated"] = True
        
        # Fetch user profile using access token
        headers = {"Authorization": f"Bearer {access_token}"}
        user_response = requests.get(f"{API_BASE_URL}/user", headers=headers)
        
        if user_response.status_code == 200:
            user_info = user_response.json().get("user", {})
            st.session_state["first_name"] =    user_info.get("first_name", "")
            st.session_state["last_name"] =    user_info.get("last_name", "")
            st.session_state["name"] = user_info.get("name", "")
        return True, "Login successful!"
    return False, "Invalid username or password"

def logout_user():
    for key in ["access_token", "refresh_token", "email", "is_authenticated"]:
        if key in st.session_state:
            del st.session_state[key]