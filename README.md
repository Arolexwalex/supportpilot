# SupportPilot

An AI-powered customer support assistant that answers questions using Retrieval-Augmented Generation (RAG) over a company's own help-center documentation — built end-to-end from planning through production deployment and monitoring.

**Live demo:** [https://supportpilot-r3t5.onrender.com/docs](https://supportpilot-r3t5.onrender.com/docs)

## What it does

SupportPilot answers customer questions by retrieving relevant chunks from a knowledge base and generating a grounded, natural-sounding answer — rather than relying on an LLM's general knowledge, which could be outdated or simply wrong for a specific company's policies.

## Architecture

User → Streamlit chat UI → FastAPI /ask endpoint (auth + rate limit)
→ retrieve() searches ChromaDB for relevant chunks
→ generate_answer_stream() streams a grounded answer back
→ Gemini (primary) → automatic fallback to Groq if Gemini is unavailable
→ sources logged server-side only, never exposed to the client


## Key features

- **RAG pipeline**: document ingestion, chunking, embeddings, and vector search via ChromaDB
- **Streaming responses**: answers appear progressively, not after a long silent wait
- **Multi-provider resilience**: automatically fails over from Gemini to Groq if the primary provider is overloaded or unavailable — verified with a real forced-failure test, not just assumed
- **Authenticated, rate-limited API**: API key auth and per-minute rate limiting on the public endpoint
- **Continuous monitoring**: a scheduled GitHub Actions workflow runs a real synthetic check (not just a shallow health ping) every 15 minutes, alerting via Slack on failure
- **Full operational documentation**: architecture notes, a runbook, an SOP, and a risk assessment (see `docs-admin/`)

## Tech stack

Python · FastAPI · Google Gemini API · Groq · ChromaDB · Streamlit · Docker · GitHub Actions · Render

## Running it locally

```bash
git clone https://github.com/your-username/supportpilot.git
cd supportpilot
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```
Create a `.env` file with:

GOOGLE_API_KEY=your-key
GROQ_API_KEY=your-key
SUPPORTPILOT_API_KEY=your-own-chosen-key
SLACK_WEBHOOK_URL=your-webhook

Then:
```bash
python app/ingest.py
uvicorn app.main:app --reload
```
In a second terminal:
```bash
streamlit run ui.py
```

## Running with Docker

```bash
docker build -t supportpilot .
docker run -p 8000:8000 --env-file .env supportpilot
```

## Testing

```bash
python -m pytest
python eval.py
```

## Project documentation

See `docs-admin/` for the architecture note, runbook, SOP, and risk assessment written for this system.