import streamlit as st
from gtts import gTTS, langs
from io import BytesIO
import os
import json
import requests
from groq import Groq
from typing import Generator
from mtranslate import translate

def text2audio():
    def text2audio_module():
        # Initialize Groq client
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        model = "mixtral-8x7b-32768"

        # Ensure directory for user data exists
        username = st.session_state.get('username', 'default_user')  # Default to 'default_user' if not set
        user_data_dir = os.path.join("DataHistory", username, "Text2Audio")
        audio_dir = os.path.join(user_data_dir, "audio")
        os.makedirs(audio_dir, exist_ok=True)

        # Initialize history list as a local variable instead of session_state
        history = []

        # Function to query the Hugging Face model for audio generation
        def query_meta_audio(prompt, headers):
            API_URL = st.secrets["META_API_KEY"]
            response = requests.post(API_URL, headers=headers, json={"inputs": prompt})
            if response.status_code == 200:
                return response.content, response.status_code
            else:
                st.write(f"Error: Received status code {response.status_code}")
                st.write(f"Response text: {response.text}")
                return None, response.status_code

        # Function to generate audio from a prompt
        def audio_generation(input_prompt):
            api_key = st.secrets["api_key"]
            headers = {"Authorization": f"Bearer {api_key}"}
            audio_bytes, status_code = query_meta_audio(input_prompt, headers)

            if audio_bytes:
                # Save audio to a local file
                audio_filename = f"{len(history)}_{username}_{input_prompt[:10]}.wav"
                audio_path = os.path.join(audio_dir, audio_filename)
                with open(audio_path, "wb") as audio_file:
                    audio_file.write(audio_bytes)

                # Store audio history entry
                history.append({"role": "assistant", "content": f"Generated audio based on prompt: {input_prompt}", "audio": audio_filename})

                # Display audio and download link
                audio_stream = BytesIO(audio_bytes)
                with st.chat_message("assistant"):
                    st.audio(audio_stream, format="audio/wav")
                    st.download_button(label="Download Audio", data=audio_stream, file_name=audio_filename, mime="audio/wav")
            else:
                error_msg = "Failed to generate audio - empty response."
                history.append({"role": "assistant", "content": error_msg})
                with st.chat_message("assistant"):
                    st.write(error_msg)

        # Template function to format the keyword prompt for Groq
        def template(input):
            prompt = f"Generate a very small prompt for an audio clip based on the keyword(s): {input}"
            return prompt

        # Function to process streaming responses from Groq's completion
        def generate_chat_responses(chat_completion) -> Generator[str, None, None]:
            for chunk in chat_completion:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        # Sidebar options to enter keywords and generate a descriptive prompt
        st.sidebar.markdown("Use this option to generate descriptive prompt 👇")
        if prompt := st.sidebar.chat_input("Enter keyword for audio prompt..."):
            descriptive_prompt = template(prompt)
            history.append({"role": "user", "content": descriptive_prompt})

            # Generate a descriptive prompt using Groq
            try:
                chat_completion = client.chat.completions.create(
                    model=model,
                    messages=[{"role": m["role"], "content": m["content"]} for m in history],
                    max_tokens=100,
                    stream=True
                )
                chat_responses_generator = generate_chat_responses(chat_completion)
                full_response = "".join(list(chat_responses_generator))
                st.sidebar.write("Generated Prompt:", full_response)
                history.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"Error generating prompt with Groq: {e}")

        # Option to clear chat history
        if st.sidebar.button('Clear Chat History'):
            history.clear()

        # Display existing chat history
        for message in history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                if "audio" in message:
                    st.audio(os.path.join(audio_dir, message["audio"]), format="audio/wav")

        # Get user input and generate audio if a prompt is provided
        prompt = st.chat_input("Describe the audio you want")
        if prompt:
            history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(f"You: {prompt}")
            with st.spinner('Generating audio...'):
                audio_generation(prompt)

    def text2speech_module():
        # Load languages dynamically from the JSON file
        languages_path = os.path.join('models', 'res', 'languages.json')
        with open(languages_path, 'r') as file:
            data = json.load(file)

        lang_array = {item['name']: item['iso'] for item in data['languages']}

        st.header("Language Translation", divider="rainbow")
        st.markdown("Translate text to a selected language and generate speech")

        # User input for translation and TTS
        input_text = st.text_area("Enter text to translate and convert to speech:", height=150)
        target_language = st.selectbox("Select target language:", list(lang_array.keys()))

        if st.button("Translate & Generate Speech"):
            if input_text:
                # Translation
                translation = translate(input_text, lang_array[target_language])
                st.text_area("Translated Text", translation, height=150)

                # Text-to-Speech
                if lang_array[target_language] in langs._langs:  # Check if language is supported by gTTS
                    audio_stream = BytesIO()
                    tts = gTTS(text=translation, lang=lang_array[target_language])
                    tts.write_to_fp(audio_stream)
                    audio_stream.seek(0)

                    # Display audio player
                    st.audio(audio_stream, format="audio/wav")

                    # Download option
                    st.download_button(label="Download Audio", data=audio_stream, file_name="translated_speech.wav",
                                       mime="audio/wav")
                else:
                    st.warning("Text-to-Speech is not supported in the selected language.")
            else:
                st.warning("Please enter some text to translate.")

    option = st.sidebar.selectbox("Select an option", ("Text to Speech", "Text to audio"))

    if option != "Text to audio":
        text2speech_module()
    else:
        text2audio_module()

