import os
import joblib
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import time
from datetime import datetime


def gemini_chat():
    load_dotenv()
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    MODEL_ROLE = 'ai'
    AI_AVATAR_ICON = '✨'

    # Define the data directory
    data_dir = 'data'

    # Create the data/ folder if it doesn't already exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    # Load past chats (if available)
    past_chats_file = os.path.join(data_dir, 'past_chats_list')
    try:
        past_chats = joblib.load(past_chats_file)
    except FileNotFoundError:
        past_chats = {}

    # Sidebar allows a list of past chats and new chat button
    with st.sidebar:
        # Handle "New Chat" button separately
        if st.button('New Chat'):
            st.session_state.current_time = current_time
            st.session_state.chat_title = f'ChatSession-{st.session_state.current_time}'
            st.session_state.messages = []
            st.session_state.gemini_history = []
            st.session_state.model = genai.GenerativeModel('gemini-pro')
            st.session_state.chat = st.session_state.model.start_chat(
                history=st.session_state.gemini_history,
            )
            past_chats[st.session_state.current_time] = st.session_state.chat_title
            joblib.dump(past_chats, past_chats_file)
        st.write('# Previous Chats 👇')
        # Display past chats as a dropdown
        if st.session_state.get('current_time') is None:
            st.session_state.current_time = st.selectbox(
                label='Chat History',
                options=list(past_chats.keys()),
                format_func=lambda x: past_chats.get(x, 'New Chat'),
                placeholder='Select or click "New Chat"',
            )
        else:
            st.session_state.current_time = st.selectbox(
                label='Pick a past chat',
                options=[st.session_state.current_time] + list(past_chats.keys()),
                format_func=lambda x: past_chats.get(x,
                                                     'New Chat' if x != st.session_state.current_time else st.session_state.chat_title),
                placeholder='Select or click "New Chat"',
            )
            st.markdown(f"Selected: {st.session_state.current_time}")

        # Save selected chat title
        st.session_state.chat_title = f'ChatSession-{st.session_state.current_time}'

        # Buttons to clear chat history and delete all chats
        col1, col2 = st.columns(2)
        with col1:
            if st.button('Delete this Chat'):
                if st.session_state.current_time in past_chats:
                    del past_chats[st.session_state.current_time]
                    joblib.dump(past_chats, past_chats_file)
                st_messages_file = os.path.join(data_dir, f'{st.session_state.current_time}-st_messages')
                gemini_messages_file = os.path.join(data_dir, f'{st.session_state.current_time}-gemini_messages')
                if os.path.exists(st_messages_file):
                    os.remove(st_messages_file)
                if os.path.exists(gemini_messages_file):
                    os.remove(gemini_messages_file)
                st.session_state.messages = []
                st.session_state.gemini_history = []
                st.session_state.current_time = None
                st.experimental_rerun()

        with col2:
            if st.button('Delete All Chats'):
                for chat_id in past_chats.keys():
                    st_messages_file = os.path.join(data_dir, f'{chat_id}-st_messages')
                    gemini_messages_file = os.path.join(data_dir, f'{chat_id}-gemini_messages')
                    if os.path.exists(st_messages_file):
                        os.remove(st_messages_file)
                    if os.path.exists(gemini_messages_file):
                        os.remove(gemini_messages_file)
                past_chats.clear()
                joblib.dump(past_chats, past_chats_file)
                st.session_state.messages = []
                st.session_state.gemini_history = []
                st.session_state.current_time = None
                st.experimental_rerun()

    st.write('# Chat with Gemini💭')

    # Load chat history if available
    try:
        st.session_state.messages = joblib.load(
            os.path.join(data_dir, f'{st.session_state.current_time}-st_messages')
        )
        st.session_state.gemini_history = joblib.load(
            os.path.join(data_dir, f'{st.session_state.current_time}-gemini_messages')
        )
    except FileNotFoundError:
        st.session_state.messages = []
        st.session_state.gemini_history = []

    # Initialize Gemini model and chat session
    if 'model' not in st.session_state:
        st.session_state.model = genai.GenerativeModel('gemini-pro')
        st.session_state.chat = st.session_state.model.start_chat(
            history=st.session_state.gemini_history,
        )

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(
                name=message['role'],
                avatar=message.get('avatar'),
        ):
            st.markdown(message['content'])

    # React to user input
    if prompt := st.chat_input('Your message here...'):
        # Display user message in chat message container
        with st.chat_message('user'):
            st.markdown(prompt)

        # Add user message to chat history
        st.session_state.messages.append(
            dict(
                role='user',
                content=prompt,
            )
        )

        # Send message to AI
        response = st.session_state.chat.send_message(
            prompt,
            stream=True,
        )

        # Display assistant response in chat message container
        with st.chat_message(
                name=MODEL_ROLE,
                avatar=AI_AVATAR_ICON,
        ):
            message_placeholder = st.empty()
            full_response = ''
            assistant_response = response

            # Streams in a chunk at a time
            for chunk in response:
                for ch in chunk.text.split(' '):
                    full_response += ch + ' '
                    time.sleep(0.05)
                    message_placeholder.write(full_response + '▌')

            # Write full message with placeholder
            message_placeholder.write(full_response)

        # Add assistant response to chat history
        st.session_state.messages.append(
            dict(
                role=MODEL_ROLE,
                content=st.session_state.chat.history[-1].parts[0].text,
                avatar=AI_AVATAR_ICON,
            )
        )
        st.session_state.gemini_history = st.session_state.chat.history

        # Save chat history to files
        joblib.dump(
            st.session_state.messages,
            os.path.join(data_dir, f'{st.session_state.current_time}-st_messages'),
        )
        joblib.dump(
            st.session_state.gemini_history,
            os.path.join(data_dir, f'{st.session_state.current_time}-gemini_messages'),
        )
