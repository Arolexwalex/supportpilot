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

def alert_slack(message):
    requests.post(os.environ["SLACK_WEBHOOK_URL"], json={"text": message})

check_health()