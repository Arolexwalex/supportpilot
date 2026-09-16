# ui.py
import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Nimbus SupportPilot", page_icon="🤖")
st.title("🤖 Nimbus SupportPilot")
st.caption("Ask a question about our services")

def get_config(key, default=None):
    try:
         if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)

API_URL = get_config("API_URL", "http://127.0.0.1:8000/ask")
API_KEY = get_config("SUPPORTPILOT_API_KEY")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"].replace("$", "\\$"))

if question := st.chat_input("Ask a question..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_text = ""
        try:
            response = requests.post(
                API_URL,
                params={"question": question},
                headers={"x-api-key": API_KEY},
                stream=True
            )
            if response.status_code == 200:
                for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                    full_text += chunk
                    placeholder.markdown(full_text.replace("$", "\\$"))
            else:
                full_text = f"Error {response.status_code}: {response.text}"
                placeholder.error(full_text)
        except requests.exceptions.ConnectionError:
            full_text = "Could not reach the SupportPilot API. Is it running?"
            placeholder.error(full_text)

    st.session_state.messages.append({"role": "assistant", "content": full_text})