# Pangolin

An AI-powered scam-detection assistant that helps everyday Nigerians recognize fraudulent job offers, investment schemes, and online listings — available on the web, Telegram, and WhatsApp.

**Live demo:** [https://supportpilot-r3t5.onrender.com/docs](https://supportpilot-r3t5.onrender.com/docs)
**Telegram:** search for the Pangolin bot
**Web app:** your Streamlit Cloud link

## The problem

Nigerians lost an estimated $1 billion to a single Ponzi scheme (CBEX) in 2025 alone. The SEC reports ₦300.2 billion lost to fraudulent investment schemes. Nearly 60% of Nigerian internet users have encountered an online scam, according to the NCC. Scammers increasingly use AI-generated deepfakes of real public figures to lend fake credibility to fraudulent offers.

## What Pangolin does

Paste in a suspicious job offer, investment pitch, or listing, and Pangolin analyzes it two ways at once:

1. **A deterministic pattern engine** — a transparent, weighted checklist of documented Nigerian scam tactics (upfront fees, unrealistic returns, urgency pressure, requests for sensitive information, impersonation of banks or government agencies), written in plain code, not left to AI guesswork.
2. **An independent AI risk assessment** — a second signal evaluating the manipulation tactics in the message's language and framing, shown alongside the pattern results rather than replacing them.

Both signals are combined transparently into one risk score and explanation — in plain English or Nigerian Pidgin — so the reasoning is always visible, never a black box.

Pangolin can also answer general questions about common scam types and how to report fraud, and correctly tells the difference between a message that needs checking and a normal greeting or question.

## Why this design

- **The scam classification is never left entirely to the AI.** The pattern engine is deterministic and auditable; the AI only adds a second, clearly-labeled opinion.
- **Privacy by design.** No message content is stored beyond what's needed to generate a response.
- **Honest disclaimers.** Pangolin flags patterns — it never asserts a message definitely is fraud, and always recommends independent verification and official reporting channels (EFCC, NCC).
- **Multi-provider resilience.** If the primary AI provider (Gemini) is unavailable, Pangolin automatically falls back to a second provider (Groq), tested under a real, unplanned quota exhaustion during development.

## Tech stack

Python · FastAPI · Google Gemini · Groq · ChromaDB (RAG) · Telegram Bot API · Twilio WhatsApp Sandbox · Streamlit · Docker · GitHub Actions · Render

## Running it locally

```bash
git clone https://github.com/your-username/supportpilot.git
cd supportpilot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
Create `.env` with `GOOGLE_API_KEY`, `GROQ_API_KEY`, `SUPPORTPILOT_API_KEY`, `SLACK_WEBHOOK_URL`, `TELEGRAM_BOT_TOKEN`, then:
```bash
python app/ingest.py
uvicorn app.main:app --reload
```

## Roadmap

Live verification against official registries (CAC, SEC) is a clear next step beyond this submission's scope — the current pattern-and-AI approach is intentionally the fast, reliable core to validate first.