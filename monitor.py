import requests, os
from dotenv import load_dotenv

load_dotenv()

def check_health():
    try:
        response = requests.get("https://supportpilot-r3t5.onrender.com/health", timeout=10)
        if response.status_code != 200:
            alert_slack(f"SupportPilot health check failed: {response.status_code}")
    except requests.exceptions.RequestException as e:
        alert_slack(f"SupportPilot unreachable: {e}")
def check_ask_works():
    try:
        response = requests.post(
            "https://supportpilot-r3t5.onrender.com/ask",
            params={"question": "What are your support hours?"},
            headers={"x-api-key": os.environ["SUPPORTPILOT_API_KEY"]},
            timeout=30
        )
        if response.status_code != 200:
            alert_slack(f"SupportPilot /ask is broken: {response.status_code} — {response.text[:200]}")
    except requests.exceptions.RequestException as e:
        alert_slack(f"SupportPilot /ask unreachable: {e}")
        
def alert_slack(message):
    requests.post(os.environ["SLACK_WEBHOOK_URL"], json={"text": message})

check_health()