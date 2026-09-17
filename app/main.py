from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import os, logging, sys
from dotenv import load_dotenv
from app.rag import generate_answer_stream

load_dotenv()
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()

def get_api_key_identity(request: Request):
    return request.headers.get("x-api-key", "anonymous")

limiter = Limiter(key_func=get_api_key_identity)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

VALID_API_KEY = os.environ["SUPPORTPILOT_API_KEY"]

@app.post("/ask")
@limiter.limit("10/minute")
def ask(request: Request, question: str, x_api_key: str = Header(...)):
    if x_api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    logging.info(f"Question received: {question[:50]}...")
    return StreamingResponse(generate_answer_stream(question), media_type="text/plain")

@app.get("/health")
def health():
    return {"status": "ok"}