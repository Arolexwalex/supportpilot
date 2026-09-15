# SupportPilot Architecture

User → Streamlit UI → FastAPI /ask endpoint (auth + rate limit)
     → retrieve() searches ChromaDB for relevant chunks
     → generate_answer_stream() sends question + chunks to Gemini API
     → streamed response returned to UI
     → sources logged server-side only (not sent to client)

Dependencies: Google Gemini API, ChromaDB (rebuilt on container start), Slack webhook (monitoring)
Hosting: Render (free tier), backend at https://supportpilot-r3t5.onrender.com
Failure points: Gemini API outage/deprecation, Render cold starts, rate limit exhaustion