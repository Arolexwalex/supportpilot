# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200

def test_ask_requires_auth():
    response = client.post("/ask", params={"question": "test"})
    assert response.status_code == 422