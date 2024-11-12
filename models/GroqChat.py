import os
import joblib
import streamlit as st
from typing import Generator
from groq import Groq
from datetime import datetime
from dotenv import load_dotenv
import shutil

def chat_groq():
    load_dotenv()
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def icon(emoji: str):
        """Shows an emoji as a Notion-style page icon."""
        st.write(
            f'<span style="font-size: 78px; line-height: 1">{emoji}</span>',
            unsafe_allow_html=True,
        )

    # Define user and directory paths
    username = st.session_state['username']
    base_chat_dir = os.path.join("DataHistory", username, "Chat")  # Updated path here
    os.makedirs(base_chat_dir, exist_ok=True)
    history_file = os.path.join(base_chat_dir, 'past_chats.pkl')

    # Unique session initialization
    if "session_id" not in st.session_state:
        st.session_state.session_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_time" not in st.session_state:
        st.session_state.current_time = None
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = None

    # Load past chats
    past_chats = joblib.load(history_file) if os.path.exists(history_file) else {}

    icon("🗪")
    st.subheader("Chat App", divider="rainbow", anchor=False)
    st.markdown("**Powered by Groq**")

    # Define available models
    models = {
        "gemma-7b-it": {"name": "Gemma-7b-it", "tokens": 8192, "developer": "Google"},
        "Gemma2-9b-it": {"name": "Gemma2-9b-it", "tokens": 8192, "developer": "Google"},
        "mixtral-8x7b-32768": {"name": "Mixtral-8x7b-Instruct-v0.1", "tokens": 32768, "developer": "Mistral"},
    }

    # Sidebar options for new and previous chats
    with st.sidebar:
        if st.button("New Chat"):
            st.session_state.current_time = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            chat_dir = os.path.join(base_chat_dir, st.session_state.current_time)
            os.makedirs(chat_dir, exist_ok=True)
            st.session_state.messages = []
            past_chats[st.session_state.current_time] = st.session_state.current_time
            joblib.dump(past_chats, history_file)

        st.write("## Previous Chats")
        selected_chat = st.selectbox("Choose a chat", list(past_chats.keys()), format_func=lambda x: past_chats[x])

        # Load selected chat history only if it exists
        if selected_chat:
            chat_file = os.path.join(base_chat_dir, selected_chat, "messages.pkl")
            if os.path.exists(chat_file):
                st.session_state.messages = joblib.load(chat_file)
            else:
                st.session_state.messages = []

        if st.button('Delete All Chats'):
            for chat_id in list(past_chats.keys()):
                chat_dir = os.path.join(base_chat_dir, chat_id)
                if os.path.exists(chat_dir):
                    shutil.rmtree(chat_dir)
            past_chats.clear()
            joblib.dump(past_chats, history_file)
            st.session_state.messages = []
            st.session_state.current_time = None
            st.rerun()

    # Model selection and tokens slider
    col1, col2 = st.columns(2)
    with col1:
        model_option = st.selectbox(
            "Choose a model:",
            options=list(models.keys()),
            format_func=lambda x: models[x]["name"],
            index=2
        )

    if st.session_state.selected_model != model_option:
        st.session_state.messages = []
        st.session_state.selected_model = model_option

    max_tokens_range = models[model_option]["tokens"]
    with col2:
        max_tokens = st.slider(
            "Max Tokens:",
            min_value=512,
            max_value=max_tokens_range,
            value=min(32768, max_tokens_range),
            step=512,
            help=f"Adjust max tokens for response. Max: {max_tokens_range}"
        )

    # Display chat history with avatars
    for message in st.session_state.messages:
        avatar = "🤖" if message["role"] == "assistant" else "👨‍💻"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # Define response generator function
    def generate_chat_responses(chat_completion) -> Generator[str, None, None]:
        for chunk in chat_completion:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    # Process user input and generate response
    if prompt := st.chat_input("Enter your prompt here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar='👨‍💻'):
            st.markdown(prompt)

        try:
            chat_completion = client.chat.completions.create(
                model=model_option,
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
                max_tokens=max_tokens,
                stream=True
            )

            # Stream and display response
            with st.chat_message("assistant", avatar="🤖"):
                chat_responses_generator = generate_chat_responses(chat_completion)
                full_response = st.write_stream(chat_responses_generator)

        except Exception as e:
            st.error(f"Error: {e}")

        # Append response to history and save
        if isinstance(full_response, str):
            st.session_state.messages.append({"role": "assistant", "content": full_response})
        else:
            combined_response = "\n".join(str(item) for item in full_response)
            st.session_state.messages.append({"role": "assistant", "content": combined_response})

        # Save the session messages only if `current_time` is set
        if st.session_state.current_time:
            chat_dir = os.path.join(base_chat_dir, st.session_state.current_time)
            os.makedirs(chat_dir, exist_ok=True)  # Ensure chat directory exists
            joblib.dump(st.session_state.messages, os.path.join(chat_dir, "messages.pkl"))
