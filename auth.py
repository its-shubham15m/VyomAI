import streamlit as st
import bcrypt
import yaml
from yaml.loader import SafeLoader
import os
import time

# Function to load config
def load_config():
    with open("config.yaml") as file:
        return yaml.load(file, Loader=SafeLoader)

# Function to save config
def save_config(config_data):
    with open("config.yaml", "w") as file:
        yaml.dump(config_data, file)

# Hash the password using bcrypt
def hash_password(password):
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    return hashed_password

# Verify the password using bcrypt
def verify_password(stored_password, entered_password):
    return bcrypt.checkpw(entered_password.encode('utf-8'), stored_password.encode('utf-8'))

# Signup function
def signup():
    st.subheader("Sign Up")
    
    # Collect user information
    new_name = st.text_input("Enter Name", key="name", help="Your full name")
    new_email = st.text_input("Enter Email", key="email", help="Your email address")
    new_username = st.text_input("Enter Username", key="username", help="Your desired username")
    new_password = st.text_input("Enter Password", type="password", key="password", help="Your password")

    if st.button("Register"):
        if new_name and new_email and new_username and new_password:
            # Hash the password
            hashed_password = hash_password(new_password)
            
            # Load current config
            config = load_config()

            # Add new user details to the config
            config["credentials"]["usernames"][new_username] = {
                "name": new_name,
                "email": new_email,
                "password": hashed_password
            }

            # Save updated config
            save_config(config)
            st.success("User registered successfully. Please log in.")
            time.sleep(2)
            st.rerun()  # Reload the app to apply new config

        else:
            st.error("Please fill in all fields.")

# Login function
def login():
    st.title("Login")
    config = load_config()

    # Login form inputs
    username = st.text_input("Username", key="login_username", help="Enter your username")
    password = st.text_input("Password", type="password", key="login_password", help="Enter your password")

    if st.button("Login"):
        if username and password:
            if username in config["credentials"]["usernames"]:
                stored_password = config["credentials"]["usernames"][username]["password"]
                if verify_password(stored_password, password):
                    st.session_state.username = username
                    st.session_state.logged_in = True
                    # Get the full name of the logged-in user
                    full_name = config["credentials"]["usernames"][username]["name"]
                    st.session_state.full_name = full_name  # Store the full name in session state
                    st.success(f"Welcome, {full_name}")
                    st.rerun()  # Reload to redirect to the main app
                else:
                    st.error("Invalid username or password.")
            else:
                st.error("Username not found.")
        else:
            st.error("Please enter both username and password.")

# Logout function
def logout():
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.full_name = None  # Clear full name on logout
    st.success("You have been logged out.")
    st.rerun()
