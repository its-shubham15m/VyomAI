import streamlit as st
import requests
import os
import pickle
import pandas as pd
from datetime import datetime

def audio_spectrogram():
    # Check if the user is logged in
    if 'username' not in st.session_state:
        st.error("You must log in to access this feature.")
        return

    # Helper function to get user-specific directory
    def get_user_data_directory():
        username = st.session_state['username']
        if username:
            user_data_dir = os.path.join("DataHistory", username, "AudioSpectrogram")
            if not os.path.exists(user_data_dir):
                try:
                    os.makedirs(user_data_dir)
                except Exception as e:
                    st.error(f"Error creating directory: {e}")
                    return None
            return user_data_dir
        return None

    # Get user-specific data directory
    user_data_dir = get_user_data_directory()
    
    if user_data_dir is None:
        st.error("Failed to create or access the user data directory.")
        return

    # Directory and history file path setup
    audio_dir = os.path.join(user_data_dir, 'audio_files')  # Folder to save audio files
    history_file_path = os.path.join(user_data_dir, "audio_history.json")
    pickle_file_path = os.path.join(user_data_dir, "audio_history.pkl")

    # Ensure directories exist
    if not os.path.exists(audio_dir):
        try:
            os.makedirs(audio_dir)
        except Exception as e:
            st.error(f"Error creating audio directory: {e}")
            return

    # Load chat history (from pickle if available)
    if 'session_history' not in st.session_state:
        st.session_state.session_history = []
        if os.path.exists(pickle_file_path):
            with open(pickle_file_path, "rb") as f:
                st.session_state.session_history = pickle.load(f)

    # Function to query the Hugging Face model
    def query_audio_model(audio_data):
        try:
            API_URL = st.secrets["AST_API_KEY"]
            headers = {"Authorization": f"Bearer {st.secrets['api_key']}"}
            response = requests.post(API_URL, headers=headers, data=audio_data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as err:
            st.error(f"Error querying audio model: {err}")
            return None

    # Function to clear chat history
    def clear_chat_history():
        # Clear session state history
        st.session_state.session_history = []

        # Remove pickle file to clear saved history
        if os.path.exists(pickle_file_path):
            os.remove(pickle_file_path)

        st.success("Chat history cleared!")

    # Function to save audio data and predictions to pickle
    def save_audio_data(audio_filename, predictions, confidences):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        audio_data = {
            "audio_filename": audio_filename,
            "predictions": predictions,
            "confidences": confidences,
            "timestamp": timestamp
        }
        # Append to session history
        st.session_state.session_history.append(audio_data)

        # Save session history to pickle
        with open(pickle_file_path, "wb") as f:
            pickle.dump(st.session_state.session_history, f)

    # UI setup
    st.header("Audio Spectrogram Analysis 🎶", divider="rainbow")
    st.sidebar.button("Clear Chat History", on_click=clear_chat_history)

    # Sidebar for file upload
    st.sidebar.header("Upload Audio")
    uploaded_audio_file = st.sidebar.file_uploader("Upload an audio file (.wav, .mp3, .flac)", type=["wav", "mp3", "flac"])

    # Audio Input using st.audio_input (for direct recording)
    st.write("Record a voice message 🎤")
    audio_value = st.audio_input("Record a voice message")

    # Handle the recorded audio input
    if audio_value:
        st.audio(audio_value, format="audio/wav")  # Play the recorded audio
        st.write("Analyzing recorded audio...")

        # Generate unique filename for the recorded audio
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        audio_filename = f"audio_{timestamp}.wav"
        audio_filepath = os.path.join(audio_dir, audio_filename)

        # Save the recorded audio as a file
        with open(audio_filepath, "wb") as f:
            f.write(audio_value.getvalue())  # Use getvalue() to retrieve bytes

        # Analyze audio using Hugging Face model
        with st.spinner("Analyzing audio..."):
            result = query_audio_model(audio_value)

        # Handle and display results
        if result:
            if isinstance(result, list):
                predictions = [entry.get("label") for entry in result]
                confidences = [entry.get("score") for entry in result]
            else:
                predictions = []
                confidences = []

            # Save audio data, predictions, and confidences as pkl
            save_audio_data(audio_filename, predictions, confidences)

            st.write("Audio analysis result:")
            if predictions and confidences:
                df = pd.DataFrame({"Label": predictions, "Confidence": confidences})
                st.table(df)
        else:
            st.write("Failed to analyze audio.")

    # If file uploaded via sidebar, handle the file upload
    if uploaded_audio_file:
        audio_data = uploaded_audio_file.read()  # Read the uploaded file as bytes
        st.sidebar.audio(audio_data, format=uploaded_audio_file.type)

        # Generate unique filename for the uploaded audio
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        audio_filename = f"audio_{timestamp}.mp3"
        audio_filepath = os.path.join(audio_dir, audio_filename)

        # Save the uploaded audio file
        with open(audio_filepath, "wb") as f:
            f.write(audio_data)  # Save the uploaded audio as bytes

        # Analyze audio using Hugging Face model
        with st.spinner("Analyzing uploaded audio..."):
            result = query_audio_model(audio_data)

        # Handle and display results
        if result:
            if isinstance(result, list):
                predictions = [entry.get("label") for entry in result]
                confidences = [entry.get("score") for entry in result]
            else:
                predictions = []
                confidences = []

            # Save audio data, predictions, and confidences as pkl
            save_audio_data(audio_filename, predictions, confidences)

            st.write("Audio analysis result:")
            if predictions and confidences:
                df = pd.DataFrame({"Label": predictions, "Confidence": confidences})
                st.table(df)
        else:
            st.write("Failed to analyze audio.")

    # Display chat history in tabular format (if needed)
    st.write("### Chat History")
    if st.session_state.session_history:
        # Convert session history to a pandas DataFrame for tabular display
        chat_data = []
        for message in st.session_state.session_history:
            if "audio_filename" in message:
                chat_data.append({
                    "Audio Filename": message['audio_filename'],
                    "Timestamp": message['timestamp'],
                    "Predictions": message['predictions'],
                    "Confidence": message['confidences']
                })
            else:
                chat_data.append({
                    "Role": message['role'],
                    "Content": message['content'],
                    "Output": message.get('output', 'N/A')
                })
        
        # Create a DataFrame and display it as a table
        chat_df = pd.DataFrame(chat_data)
        st.table(chat_df)
