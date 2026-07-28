import os
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
DATA_DIR = "/Users/pooja/Documents/GitHub/enterprise-knowledge-assistant/data"


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_upload_pdf_endpoint():
    pdf_path = os.path.join(DATA_DIR, "HR", "LeavePolicy.pdf")
    assert os.path.exists(pdf_path)

    with open(pdf_path, "rb") as f:
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("LeavePolicy.pdf", f, "application/pdf")},
            data={
                "title": "HR Leave Policy 2026",
                "department": "HR",
                "security_level": "Confidential",
                "allowed_roles": "HR, Executive",
                "owner": "HR Admin"
            }
        )

    assert response.status_code == 201
    data = response.json()
    assert "doc_id" in data
    assert data["chunk_count"] >= 1
    assert data["metadata"]["department"] == "HR"
    assert data["metadata"]["security_level"] == "Confidential"

    # Verify listing
    list_res = client.get("/api/v1/documents")
    assert list_res.status_code == 200
    docs = list_res.json()["documents"]
    assert any(d["doc_id"] == data["doc_id"] for d in docs)
