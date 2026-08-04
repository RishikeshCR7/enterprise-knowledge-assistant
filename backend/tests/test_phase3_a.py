import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.eval_db import eval_db
from app.utils.observability import TelemetryTracker

client = TestClient(app)


def test_eval_db_operations(tmp_path):
    # Test evaluation persistence
    eval_db.insert_evaluation(
        query="What is the leave policy?",
        answer="20 days annual leave",
        faithfulness=0.95,
        answer_relevancy=0.98,
        context_precision=0.90,
        context_recall=0.92,
        hallucination_rate=0.05,
        latency_ms=120.0,
        total_tokens=300,
        cost_usd=0.0006
    )

    summary = eval_db.get_evaluation_summary()
    assert summary["total_evals"] >= 1
    assert summary["avg_faithfulness"] > 0

    recent = eval_db.get_recent_evaluations(limit=5)
    assert len(recent) >= 1


def test_telemetry_tracker():
    tracker = TelemetryTracker(trace_id="test_trace_123")
    tracker.record_stage("retrieval_ms", 15.5)
    tracker.record_stage("embedding_ms", 8.2)
    tracker.record_stage("reranker_ms", 22.0)
    tracker.record_stage("llm_ms", 110.0)
    tracker.estimate_tokens_and_cost("Sample prompt text", "Sample completion answer text")

    data = tracker.finish_and_save()
    assert data["trace_id"] == "test_trace_123"
    assert data["retrieval_ms"] == 15.5
    assert data["total_tokens"] > 0
    assert data["cost_usd"] > 0.0


def test_analytics_api_endpoints():
    # 1. Test GET /api/v1/analytics/evaluation
    eval_res = client.get("/api/v1/analytics/evaluation")
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert "summary" in eval_data
    assert "avg_faithfulness" in eval_data["summary"]

    # 2. Test GET /api/v1/analytics/cost
    cost_res = client.get("/api/v1/analytics/cost")
    assert cost_res.status_code == 200
    cost_data = cost_res.json()
    assert "total_queries" in cost_data
    assert "latency_breakdown_ms" in cost_data

    # 3. Test GET /api/v1/analytics/documents
    doc_res = client.get("/api/v1/analytics/documents")
    assert doc_res.status_code == 200
    doc_data = doc_res.json()
    assert "total_documents" in doc_data
    assert "total_chunks" in doc_data
    assert "department_distribution" in doc_data
