import streamlit as st
from streamlit_option_menu import option_menu
from models import GroqChat, ImageChat, PdfChat, Text2Image, Text2Audio, AudioSpectrogram, qr_generator, res
from PIL import Image
import os
import auth  # Import the auth.py module for handling login/logout

# Initialize session state if not already set
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = None

# App Header
path = os.path.join("models/res", "logo.png")
logo = Image.open(path)

# Sidebar Menu Example
EXAMPLE_NO = 1
st.set_page_config(page_title="VyomAI", page_icon=logo, layout="wide")
with open("style.css") as css:
    st.markdown(f'<style>{css.read()}</style>', unsafe_allow_html=True)
with st.sidebar:
    st.image("models/res/yom.png")

# Menu function for navigation
def streamlit_menu(example=1):
    if example == 1:
        with st.sidebar:
            selected = option_menu(
                menu_title="Chat Menu",  # required
                options=["Home", "Image", "Pdf", "Text 👉 Image", "Text 👉 Audio", "Audio Spectrogram", "QR Generator"],  # required
                icons=["house", "camera", "envelope", "sunset", "play", "graph-up", "box"],  # optional
                menu_icon="cast",  # optional
                default_index=0,  # optional
            )
        return selected

    elif example == 2:
        # Horizontal menu w/o custom style
        selected = option_menu(
            menu_title=None,  # required
            options=["Home", "Projects", "Contact"],  # required
            icons=["house", "book", "envelope"],  # optional
            menu_icon="cast",  # optional
            default_index=0,  # optional
            orientation="horizontal",
        )
        return selected

    elif example == 3:
        # Horizontal menu with custom style
        selected = option_menu(
            menu_title=None,  # required
            options=["Home", "Projects", "Contact"],  # required
            icons=["house", "book", "envelope"],  # optional
            menu_icon="cast",  # optional
            default_index=0,  # optional
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "orange", "font-size": "25px"},
                "nav-link": {
                    "font-size": "25px",
                    "text-align": "left",
                    "margin": "0px",
                    "--hover-color": "#eee",
                },
                "nav-link-selected": {"background-color": "green"},
            },
        )
        return selected

    return None

# If user is logged in, show models, else show login or sign-up options
if st.session_state.logged_in:
    # User is logged in, show models and options
    selected = streamlit_menu(example=EXAMPLE_NO)
    st.markdown(f"## Welcome, {st.session_state['full_name']}!\n <h5>What can I help with?", unsafe_allow_html=True)
    if selected == "Home":
        GroqChat.chat_groq()
    if selected == "Image":
        ImageChat.gemini_image_chat()
    if selected == "Pdf":
        PdfChat.gemini_pdf_chat()
    if selected == "Text 👉 Image":
        Text2Image.gemini_text2image()
    if selected == "Text 👉 Audio":
        Text2Audio.text2audio()
    if selected == "Audio Spectrogram":
        AudioSpectrogram.audio_spectrogram()
    if selected == "QR Generator":
        qr_generator.QR()

    if st.sidebar.button("Refresh 🔃"):
        st.rerun()
    # Logout option
    if st.sidebar.button("Logout"):
        auth.logout()

else:
    # User is not logged in, show login or sign-up options
    auth_choice = option_menu(
        menu_title="Choose Action",
        options=["Login", "Sign Up"],
        icons=["person-check", "person-plus"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    )

    if auth_choice == "Login":
        auth.login()

    elif auth_choice == "Sign Up":
        auth.signup()
