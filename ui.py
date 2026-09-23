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

st.set_page_config(page_title="Pangolin", page_icon="🛡️")
st.title("🛡️ Pangolin")
st.caption("Paste a suspicious message to check it, or ask a question about common Nigerian scams")

BASE_URL = get_config("API_URL", "http://127.0.0.1:8000").rstrip("/ask").rstrip("/")
API_KEY = get_config("SUPPORTPILOT_API_KEY")

mode = st.radio("What would you like to do?", ["Check a message", "Ask a question"], horizontal=True)

if mode == "Check a message":
    if "check_history" not in st.session_state:
        st.session_state.check_history = []

    with st.form("check_form", clear_on_submit=True):
        message = st.text_area("Paste the job offer, investment message, or listing here:", height=150)
        submitted = st.form_submit_button("Check this message")

    if submitted and message:
        with st.spinner("Analyzing..."):
            try:
                response = requests.post(
                    f"{BASE_URL}/check",
                    params={"message": message},
                    headers={"x-api-key": API_KEY},
                    timeout=120
                )
                if response.status_code == 200:
                    st.session_state.check_history.insert(0, {"message": message, "data": response.json(), "error": None})
                else:
                    st.session_state.check_history.insert(0, {"message": message, "data": None, "error": f"{response.status_code}: {response.text}"})
            except requests.exceptions.ConnectionError:
                st.session_state.check_history.insert(0, {"message": message, "data": None, "error": "Could not reach Pangolin backend."})

    for entry in st.session_state.check_history:
        with st.container(border=True):
            preview = entry["message"][:80] + ("..." if len(entry["message"]) > 80 else "")
            st.caption(f'Checked: "{preview}"')
            if entry["error"]:
                st.error(entry["error"])
            else:
                data = entry["data"]
                level = data["risk_level"]
                color = "🔴" if "HIGH" in level else "🟡" if "MEDIUM" in level else "🟢"
                st.markdown(f"### {color} {level} — Score: {data['score']}/100")
                if data["flags"]:
                    st.markdown("**Flags detected:**")
                    for flag in data["flags"]:
                        st.markdown(f"- {flag}")
                st.markdown("**Explanation:**")
                st.write(data["explanation"])