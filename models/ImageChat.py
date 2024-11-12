import os
import joblib
import streamlit as st
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime


def gemini_image_chat():
    load_dotenv()
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    # Function to get response from the Gemini model
    def get_gemini_response(user_input, image):
        model = genai.GenerativeModel('gemini-1.5-flash')
        if user_input:
            response = model.generate_content([user_input, image])
        else:
            response = model.generate_content(image)
        return response.text

    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    MODEL_ROLE = 'ai'
    AI_AVATAR_ICON = '✨'

    # Get the user from session state and define paths
    if 'username' not in st.session_state:
        st.error("You must be logged in to use this feature.")
        return

    username = st.session_state['username']
    user_data_dir = os.path.join("DataHistory", username, "ImageChat")

    # Create the directory if it doesn't exist
    if not os.path.exists(user_data_dir):
        os.makedirs(user_data_dir)

    # Define image and chat history directories
    images_dir = os.path.join(user_data_dir, 'images')
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    # Load past chats (if available)
    past_chats_file = os.path.join(user_data_dir, 'past_chats_list')
    try:
        past_chats = joblib.load(past_chats_file)
    except FileNotFoundError:
        past_chats = {}

    # Sidebar for past chats and new chat button
    with st.sidebar:
        if st.button('New Chat'):
            st.session_state.imagechat_current_time = current_time
            st.session_state.imagechat_chat_title = f'ChatSession-{st.session_state.imagechat_current_time}'
            st.session_state.imagechat_messages = []
            st.session_state.imagechat_gemini_history = []
            past_chats[st.session_state.imagechat_current_time] = st.session_state.imagechat_chat_title
            joblib.dump(past_chats, past_chats_file)
            st.rerun()

        st.write('# Previous Chats 👇')
        st.session_state.imagechat_current_time = st.selectbox(
            label='Chat History',
            options=list(past_chats.keys()),
            format_func=lambda x: past_chats.get(x, 'New Chat'),
            index=0,
        )
        st.session_state.imagechat_chat_title = past_chats.get(st.session_state.imagechat_current_time, 'New Chat')

        
        if st.button('Delete Chat History'):
            if st.session_state.imagechat_current_time in past_chats:
                del past_chats[st.session_state.imagechat_current_time]
                joblib.dump(past_chats, past_chats_file)
            st_messages_file = os.path.join(user_data_dir, f'{st.session_state.imagechat_current_time}-st_messages')
            gemini_messages_file = os.path.join(user_data_dir, f'{st.session_state.imagechat_current_time}-gemini_messages')
            if os.path.exists(st_messages_file):
                os.remove(st_messages_file)
            if os.path.exists(gemini_messages_file):
                os.remove(gemini_messages_file)
            st.session_state.imagechat_messages = []
            st.session_state.imagechat_gemini_history = []
            st.session_state.imagechat_current_time = None
            st.rerun()


    st.header("Chat with Image using Gemini🖼️")

    # Load chat history if available
    try:
        st.session_state.imagechat_messages = joblib.load(
            os.path.join(user_data_dir, f'{st.session_state.imagechat_current_time}-st_messages')
        )
        st.session_state.imagechat_gemini_history = joblib.load(
            os.path.join(user_data_dir, f'{st.session_state.imagechat_current_time}-gemini_messages')
        )
    except FileNotFoundError:
        st.session_state.imagechat_messages = []
        st.session_state.imagechat_gemini_history = []

    # Display chat history
    for msg in st.session_state.imagechat_messages:
        with st.chat_message(msg['role'], avatar="👨‍💻" if msg['role'] == "user" else AI_AVATAR_ICON):
            st.markdown(msg['content'])

    # Input and Image Upload
    input_text = st.chat_input("Input Prompt:", key="input_text")
    uploaded_file = st.sidebar.file_uploader("Choose an image...", type=["jpg", "jpeg", "png", "webp"])

    image = None
    image_path = None
    if uploaded_file:
        image = Image.open(uploaded_file)
        if image.format == 'WEBP':
            image = image.convert("RGB")
        file_extension = image.format.lower() if image.format else 'jpg'
        image_path = os.path.join(images_dir, f'{st.session_state.imagechat_current_time}-image.{file_extension}')
        image.save(image_path)

    # Display the uploaded image
    if image:
        st.image(image, caption="Uploaded Image", width=450)

    # "Tell me more about the image" button logic
    submit = st.sidebar.button("Tell me more about the image")

    # Generate and display response when the button is clicked
    if submit and (input_text or uploaded_file):
        if image:
            if not input_text:
                input_text = "No prompt provided."
            else:
                response = get_gemini_response(input_text, image)
            response = get_gemini_response(input_text, image)
        else:
            response = "No image provided."

        # Display response and save to session state
        st.subheader("👇 Brief Description of the Image")
        st.write(response)
        
        st.session_state.imagechat_messages.append(
            dict(role='user', content=f"Prompt: {input_text}\nImage: {uploaded_file.name if uploaded_file else 'None'}", image_path=image_path)
        )
        st.session_state.imagechat_messages.append(
            dict(role=MODEL_ROLE, content=response, avatar=AI_AVATAR_ICON)
        )
        st.session_state.imagechat_gemini_history.append(
            {"user": f"Prompt: {input_text}\nImage: {uploaded_file.name if uploaded_file else 'None'}", "ai": response}
        )

        # Save chat history
        joblib.dump(
            st.session_state.imagechat_messages,
            os.path.join(user_data_dir, f'{st.session_state.imagechat_current_time}-st_messages')
        )
        joblib.dump(
            st.session_state.imagechat_gemini_history,
            os.path.join(user_data_dir, f'{st.session_state.imagechat_current_time}-gemini_messages')
        )

    # Generate and display response when the button is clicked
    if input_text:
        if image:
            response = get_gemini_response(input_text, image)
        else:
            response = "No image provided."

        # Display response and save to session state
        st.subheader("👇 Brief Description of the Image")
        st.write(response)
        
        st.session_state.imagechat_messages.append(
            dict(role='user', content=f"Prompt: {input_text}\nImage: {uploaded_file.name if uploaded_file else 'None'}", image_path=image_path)
        )
        st.session_state.imagechat_messages.append(
            dict(role=MODEL_ROLE, content=response, avatar=AI_AVATAR_ICON)
        )
        st.session_state.imagechat_gemini_history.append(
            {"user": f"Prompt: {input_text}\nImage: {uploaded_file.name if uploaded_file else 'None'}", "ai": response}
        )

        # Save chat history
        joblib.dump(
            st.session_state.imagechat_messages,
            os.path.join(user_data_dir, f'{st.session_state.imagechat_current_time}-st_messages')
        )
        joblib.dump(
            st.session_state.imagechat_gemini_history,
            os.path.join(user_data_dir, f'{st.session_state.imagechat_current_time}-gemini_messages')
        )
