from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello Enterprise AI"}
    print("[OK] GET / passed")


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    print("[OK] GET /health passed")


def test_chat_endpoint():
    payload = {
        "question": "What is the HR leave policy?",
        "user_id": "rishi_01",
        "role": "HR",
        "department": "HR",
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["answer"] == "Coming Soon - Hello Enterprise AI"
    assert data["rewritten_query"] == "Optimized: What is the HR leave policy?"
    print("[OK] POST /api/v1/chat passed")


if __name__ == "__main__":
    test_root()
    test_health()
    test_chat_endpoint()
    print("[OK] All FastAPI endpoints verified!")
