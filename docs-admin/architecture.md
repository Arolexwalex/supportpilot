# SupportPilot Architecture

User → Streamlit UI → FastAPI /ask endpoint (auth + rate limit)
     → retrieve() searches ChromaDB for relevant chunks
     → generate_answer_stream() sends question + chunks to Gemini API
     → streamed response returned to UI
     → sources logged server-side only (not sent to client)

## Multi-provider resilience

Gemini is the primary LLM provider. If it fails after 3 retries (specifically for 503
overload errors — other failures, like an invalid model name, skip retries and fail
over immediately since retrying a non-transient error would be pointless), the system
automatically falls back to Groq (openai/gpt-oss-120b) using the same prompt, so the
user receives a complete answer regardless of which provider actually served it.

This was deliberately tested, not just assumed: the primary model was set to an
invalid name to force a guaranteed failure, and the fallback was confirmed to serve
a correct answer within ~1 second, with no visible error to the end user.

## Secrets and where they live

| Secret | .env (local) | Render | GitHub Actions | Streamlit Cloud |
|---|---|---|---|---|
| GOOGLE_API_KEY | ✅ | ✅ | ✅ | — |
| GROQ_API_KEY | ✅ | ✅ | — | — |
| SUPPORTPILOT_API_KEY | ✅ | ✅ | ✅ | ✅ |
| SLACK_WEBHOOK_URL | ✅ | — | ✅ | — |
| API_URL | ✅ (points to localhost) | — | — | ✅ (points to Render URL) |

Note: these are four genuinely separate secret stores. Updating one does not update
the others — this was learned the hard way during a 401 debugging session where the
UI's key and the backend's key had fallen out of sync.

## Dependencies
Google Gemini API, Groq API, ChromaDB (rebuilt on every container start from docs/),
Slack webhook (monitoring)

## Hosting
Backend: Render (free tier) — https://supportpilot-r3t5.onrender.com
UI: Streamlit Community Cloud

## Known failure points
- Gemini API outage or model deprecation (mitigated by Groq fallback)
- Render free-tier cold starts after inactivity (mitigated by the 15-minute scheduled monitor keeping it warm)
- Rate limit exhaustion on the /ask endpoint (10/minute, by design)