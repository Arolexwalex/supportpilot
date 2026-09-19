from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import StreamingResponse, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import os, logging, sys, requests
from xml.sax.saxutils import escape as xml_escape
from dotenv import load_dotenv
from app.rag import generate_answer_stream, client, groq_client
from app.scam_detector import check_text

load_dotenv()
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()

def get_api_key_identity(request: Request):
    return request.headers.get("x-api-key", "anonymous")

limiter = Limiter(key_func=get_api_key_identity)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

VALID_API_KEY = os.environ["SUPPORTPILOT_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def explain_result(text, result):
    if result["matched_rules"]:
        flags_text = "\n".join([f"- {r['description']}" for r in result["matched_rules"]])
    else:
        flags_text = "No known red flags were detected in the message."

    prompt = f"""You are ScamShield. A user shared this message to check: "{text}"

Automated pattern analysis found:
Risk level: {result['risk_level']} (score: {result['score']}/100)
Flags detected:
{flags_text}

Explain this result warmly and clearly, in plain English with a light natural touch of Nigerian Pidgin where it fits. Reference the specific flags found, in your own words. If risk is high or medium, gently advise caution and suggest verifying independently or reporting to the EFCC or NCC. If no flags were found, remind them that this doesn't guarantee the message is genuine — normal caution still applies. Never accuse anyone directly of being a criminal; only describe the message's characteristics."""

    try:
        response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
        return response.text
    except Exception as e:
        logging.warning(f"Gemini failed ({e}), falling back to Groq for explanation")
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}]
        )
        return completion.choices[0].message.content


@app.post("/ask")
@limiter.limit("10/minute")
def ask(request: Request, question: str, x_api_key: str = Header(...)):
    if x_api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    logging.info(f"Question received: {question[:50]}...")
    return StreamingResponse(generate_answer_stream(question), media_type="text/plain")


@app.post("/check")
@limiter.limit("10/minute")
def check(request: Request, message: str, x_api_key: str = Header(...)):
    if x_api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    result = check_text(message)
    explanation = explain_result(message, result)
    logging.info(f"Scam check: score={result['score']} level={result['risk_level']}")
    return {
        "risk_level": result["risk_level"],
        "score": result["score"],
        "flags": [r["description"] for r in result["matched_rules"]],
        "explanation": explanation
    }


@app.get("/health")
def health():
    return {"status": "ok"}


def send_telegram_message(chat_id, text):
    requests.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": text})


@app.post("/telegram-webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id or not text:
        return {"ok": True}

    if text == "/start":
        send_telegram_message(chat_id,
            "👋 Welcome to Pangolin! Paste any suspicious job offer, investment message, "
            "or listing and I'll check it for known scam red flags.")
        return {"ok": True}

    result = check_text(text)
    explanation = explain_result(text, result)
    reply = f"🛡️ {result['risk_level']} (Score: {result['score']}/100)\n\n{explanation}"
    send_telegram_message(chat_id, reply)
    return {"ok": True}


@app.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request):
    form = await request.form()
    text = form.get("Body", "")

    if not text:
        return Response(content="<Response></Response>", media_type="application/xml")

    result = check_text(text)
    explanation = explain_result(text, result)
    reply = f"ScamShield: {result['risk_level']} (Score: {result['score']}/100)\n\n{explanation}"

    twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{xml_escape(reply)}</Message></Response>'
    return Response(content=twiml, media_type="application/xml")