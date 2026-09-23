import logging
import os
import re
import sys
from xml.sax.saxutils import escape as xml_escape

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response, StreamingResponse
import requests
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.rag import client, generate_answer, generate_answer_stream, groq_client
from app.scam_detector import check_text

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="Pangolin API")

# In-memory deduplication cache for Telegram updates
processed_updates = set()

# Limiter configuration
def get_api_key_identity(request: Request):
    return request.headers.get("x-api-key", "anonymous")

limiter = Limiter(key_func=get_api_key_identity)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

VALID_API_KEY = os.environ.get("SUPPORTPILOT_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# Twilio Configuration (For WhatsApp REST API background responses)
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "")


def explain_result(text: str, result: dict) -> str:
    """
    Generates a concise, plain-text explanation grounded in the scam analysis rules & score.
    Uses strict prompt constraints for fast LLM generation times.
    """
    if result.get("matched_rules"):
        flags_text = "\n".join([f"- {r['description']}" for r in result["matched_rules"]])
    else:
        flags_text = "No direct rule matches were triggered."

    prompt = f"""You are ScamShield (Pangolin AI). A user provided this text to analyze: "{text}"

Analysis Findings:
- Matched Rule Flags:
{flags_text}
- Semantic Risk Assessment: {result.get('semantic_risk', 'UNKNOWN')} ({result.get('semantic_reasoning', 'None')})
- Overall Assessment: {result.get('risk_level', 'UNKNOWN')} (Score: {result.get('score', 0)}/100)

INSTRUCTIONS:
Explain this verdict warmly and concisely in 2-3 short plain-text paragraphs.
- Keep it under 150 words total.
- Do NOT use markdown asterisks (**), headers (#), tables, or bullet points.
- You may use a light, natural touch of Nigerian Pidgin if helpful.
- Gently advise caution and suggest verifying independently or reporting to EFCC/NCC if risk is Medium/High.
- Never directly call anyone a criminal; describe only message characteristics."""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash", 
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        logging.warning(f"Gemini generation failed ({e}), initiating fallback to Groq.")
        try:
            completion = groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=250,
            )
            return completion.choices[0].message.content.strip()
        except Exception as groq_err:
            logging.error(f"Groq fallback failed as well: {groq_err}")
            return (
                f"Risk Level: {result.get('risk_level')}. "
                "Please exercise extreme caution with this offer, as several suspicious patterns were detected."
            )


GREETING_PATTERNS = [
    r"^\s*(hi|hello|hey|good morning|good afternoon|good evening|how are you|what'?s up|thanks|thank you)\b"
]
QUESTION_STARTERS = [
    r"^\s*(what|why|how|who|when|where|is|are|can|does|do|explain|tell me)\b"
]


def looks_like_a_check_request(text: str) -> bool:
    text_lower = text.strip().lower()
    if len(text_lower) < 8:
        return False
    if any(re.match(p, text_lower) for p in GREETING_PATTERNS):
        return False
    if any(re.match(p, text_lower) for p in QUESTION_STARTERS) and len(text_lower.split()) < 12:
        return False
    return True


def send_telegram_message(chat_id: int, text: str):
    try:
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        )
    except Exception as e:
        logging.error(f"Failed to send Telegram message to {chat_id}: {e}")


def send_whatsapp_message(to_number: str, text: str):
    """Sends asynchronous WhatsApp message via Twilio REST API."""
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_PHONE_NUMBER):
        logging.error("Twilio credentials missing; cannot send background WhatsApp message.")
        return

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    data = {
        "From": TWILIO_PHONE_NUMBER,
        "To": to_number,
        "Body": text,
    }
    try:
        requests.post(url, data=data, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN), timeout=10)
    except Exception as e:
        logging.error(f"Failed to send WhatsApp message to {to_number}: {e}")


# --- Background Worker Functions ---

async def handle_telegram_message(chat_id: int, text: str):
    """Executes heavy AI inference tasks asynchronously in the background for Telegram."""
    if text == "/start":
        send_telegram_message(
            chat_id,
            "Welcome to Pangolin! Paste any suspicious job offer, investment message, "
            "or listing and I'll check it for scam red flags. Or just ask me a question.",
        )
        return

    if not looks_like_a_check_request(text):
        answer, _ = await run_in_threadpool(generate_answer, text)
        send_telegram_message(chat_id, answer)
        return

    # Execute synchronous check_text and explain_result in worker threads
    result = await run_in_threadpool(check_text, text)
    explanation = await run_in_threadpool(explain_result, text, result)
    
    reply = f"🛡️ {result['risk_level']} (Score: {result['score']}/100)\n\n{explanation}"
    send_telegram_message(chat_id, reply)


async def handle_whatsapp_message(from_number: str, text: str):
    """Executes heavy AI inference tasks asynchronously in the background for WhatsApp."""
    if not looks_like_a_check_request(text):
        answer, _ = await run_in_threadpool(generate_answer, text)
        send_whatsapp_message(from_number, answer)
        return

    result = await run_in_threadpool(check_text, text)
    explanation = await run_in_threadpool(explain_result, text, result)
    
    reply = f"Pangolin: {result['risk_level']} (Score: {result['score']}/100)\n\n{explanation}"
    send_whatsapp_message(from_number, reply)


# --- Endpoint Definitions ---

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
@limiter.limit("10/minute")
def ask(request: Request, question: str, x_api_key: str = Header(...)):
    if x_api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    logging.info(f"Question received: {question[:50]}...")
    return StreamingResponse(
        generate_answer_stream(question), media_type="text/plain"
    )


@app.post("/check")
@limiter.limit("10/minute")
async def check(request: Request, message: str, x_api_key: str = Header(...)):
    if x_api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Run heavy blocking functions off the main async thread
    result = await run_in_threadpool(check_text, message)
    explanation = await run_in_threadpool(explain_result, message, result)
    
    logging.info(f"Scam check completed: score={result['score']} level={result['risk_level']}")
    return {
        "risk_level": result["risk_level"],
        "score": result["score"],
        "flags": [r["description"] for r in result.get("matched_rules", [])],
        "explanation": explanation,
    }


@app.post("/telegram-webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    update = await request.json()

    update_id = update.get("update_id")
    if update_id:
        if update_id in processed_updates:
            return {"ok": True}
        processed_updates.add(update_id)
        if len(processed_updates) > 10000:
            processed_updates.clear()

    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id or not text:
        return {"ok": True}

    background_tasks.add_task(handle_telegram_message, chat_id, text)
    return {"ok": True}


@app.post("/whatsapp-webhook")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    form = await request.form()
    text = form.get("Body", "")
    from_number = form.get("From", "")

    if not text or not from_number:
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
            media_type="application/xml",
        )

    background_tasks.add_task(handle_whatsapp_message, from_number, text)

    return Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response></Response>',
        media_type="application/xml",
    )