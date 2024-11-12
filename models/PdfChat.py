import streamlit as st
import os
import pickle
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import asyncio
from dotenv import load_dotenv

def gemini_pdf_chat():
    load_dotenv()
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    def get_or_create_eventloop():
        try:
            return asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return asyncio.get_event_loop()

    # Initialize the event loop
    loop = get_or_create_eventloop()

    def get_pdf_text(pdf_docs):
        text = ""
        for pdf in pdf_docs:
            pdf_reader = PdfReader(pdf)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text

    def get_text_chunks(text):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
        chunks = text_splitter.split_text(text)
        return chunks

    def get_vector_store(text_chunks):
        embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
        os.makedirs("faiss_index", exist_ok=True)  # Ensure the 'faiss_index' folder exists
        vector_store.save_local("faiss_index")

    def get_conversational_chain():
        prompt_template = """
        Answer the question as detailed as possible from the provided context, make sure to provide all the details, don't provide the wrong answer\n\n
        Context:\n {context}?\n
        Question: \n{question}\n

        Answer:
        """

        model = ChatGoogleGenerativeAI(model="gemini-1.0-pro", temperature=0.3)
        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
        chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

        return chain

    def user_input(user_question):
        index_file = os.path.join("faiss_index", "index.faiss")
        if not os.path.exists(index_file):
            st.warning("Please upload and process PDF files first.")
            return None

        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        docs = new_db.similarity_search(user_question)

        chain = get_conversational_chain()
        response = chain.invoke({"input_documents": docs, "question": user_question}, return_only_outputs=True)
        return response

    def save_chat_history(username, chat_history, document_name):
        user_data_dir = os.path.join("DataHistory", username, "PdfChat", "document", document_name)
        os.makedirs(user_data_dir, exist_ok=True)

        history_file = os.path.join(user_data_dir, "chat_history.pkl")
        with open(history_file, "wb") as f:
            pickle.dump(chat_history, f)

    def load_chat_history(username, document_name):
        user_data_dir = os.path.join("DataHistory", username, "PdfChat", "document", document_name)
        history_file = os.path.join(user_data_dir, "chat_history.pkl")

        if os.path.exists(history_file):
            with open(history_file, "rb") as f:
                return pickle.load(f)
        return []

    st.header("Chat with PDFs 📚", divider="rainbow")

    username = st.session_state['username']
    pdf_docs = st.sidebar.file_uploader("Upload your PDF Files and Click on the Submit & Process Button",
                                        accept_multiple_files=True)

    # Create subdirectory for document name
    if pdf_docs:
        document_name = pdf_docs[0].name.split('.')[0]  # Use the first PDF name (without extension) as the document name
        user_data_dir = os.path.join("DataHistory", username, "PdfChat", "document", document_name)

        os.makedirs(user_data_dir, exist_ok=True)

        # Save uploaded PDFs to the document subdir (directly under PdfChat/document)
        for pdf in pdf_docs:
            file_path = os.path.join(user_data_dir, pdf.name)  # Save directly as file.pdf in PdfChat/document/
            with open(file_path, "wb") as f:
                f.write(pdf.getbuffer())

        chat_history = load_chat_history(username, document_name)

        # Display previous chat history if exists
        for message in chat_history:
            if message["sender"] == "user":
                st.chat_message(message["sender"], avatar="👨‍💻").text(message["content"])
            else:
                st.chat_message(message["sender"], avatar="🤖").text(message["content"])

        user_question = st.chat_input("Ask a Question from the PDF Files")
        if user_question:
            st.chat_message("user", avatar="👨‍💻").text(user_question)
            chat_history.append({"sender": "user", "content": user_question})

            response = user_input(user_question)
            if response:
                response_text = response["output_text"]
                st.chat_message("assistant", avatar="🤖").text(response_text)
                chat_history.append({"sender": "assistant", "content": response_text})

            save_chat_history(username, chat_history, document_name)

    with st.sidebar:
        st.title("Menu:")
        if st.button("Submit & Process"):
            with st.spinner("Processing..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks)
                st.success("Done")
