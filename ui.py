import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_config(key, default=None):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, default)

st.set_page_config(page_title="ScamShield", page_icon="🛡️")
st.title("🛡️ ScamShield")
st.caption("Paste a suspicious message to check it, or ask a question about common Nigerian scams")

BASE_URL = get_config("API_URL", "http://127.0.0.1:8000").rstrip("/ask").rstrip("/")
API_KEY = get_config("SUPPORTPILOT_API_KEY")

mode = st.radio("What would you like to do?", ["Check a message", "Ask a question"], horizontal=True)

if mode == "Check a message":
    message = st.text_area("Paste the job offer, investment message, or listing here:", height=150)
    if st.button("Check this message") and message:
        with st.spinner("Analyzing..."):
            try:
                response = requests.post(
                    f"{BASE_URL}/check",
                    params={"message": message},
                    headers={"x-api-key": API_KEY},
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    level = data["risk_level"]
                    color = "🔴" if "HIGH" in level else "🟡" if "MEDIUM" in level else "🟢"
                    st.markdown(f"### {color} {level} — Score: {data['score']}/100")
                    if data["flags"]:
                        st.markdown("**Flags detected:**")
                        for flag in data["flags"]:
                            st.markdown(f"- {flag}")
                    st.markdown("**Explanation:**")
                    st.write(data["explanation"])
                else:
                    st.error(f"Error {response.status_code}: {response.text}")
            except requests.exceptions.ConnectionError:
                st.error("Could not reach ScamShield. Is the backend running?")

else:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"].replace("$", "\\$"))

    if question := st.chat_input("Ask about common scams..."):
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_text = ""
            try:
                response = requests.post(
                    f"{BASE_URL}/ask",
                    params={"question": question},
                    headers={"x-api-key": API_KEY},
                    stream=True
                )
                if response.status_code == 200:
                    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                        full_text += chunk
                        placeholder.markdown(full_text.replace("$", "\\$"))
                else:
                    full_text = f"Error {response.status_code}"
                    placeholder.error(full_text)
            except requests.exceptions.ConnectionError:
                full_text = "Could not reach ScamShield."
                placeholder.error(full_text)

        st.session_state.messages.append({"role": "assistant", "content": full_text})