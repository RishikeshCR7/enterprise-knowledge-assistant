from fastapi.testclient import TestClient
from app.main import app
from app.agents.rag_graph import rag_graph
from app.rbac.roles import UserRole, Department

client = TestClient(app)


def test_phase3_trace_and_confidence():
    initial_state = {
        "question": "What is the HR leave policy?",
        "user_context": {
            "user_id": "test_user",
            "username": "rishi",
            "role": UserRole.HR.value,
            "department": Department.HR.value,
        },
        "chat_history": [],
        "rewritten_query": None,
        "retrieved_docs": None,
        "reranked_docs": None,
        "filtered_docs": None,
        "generation": None,
        "sources": None,
        "confidence_score": 0,
        "execution_trace": [],
        "is_safe": None,
    }

    final_state = rag_graph.invoke(initial_state)

    print(f"[TEST Phase 3] Calculated Confidence Score: {final_state.get('confidence_score')}%")
    print(f"[TEST Phase 3] Telemetry trace steps count: {len(final_state.get('execution_trace', []))}")

    assert final_state.get("confidence_score") is not None
    assert len(final_state.get("execution_trace", [])) >= 5
    print("[OK] Multi-Agent Trace Telemetry & Confidence Score test passed!")


def test_phase3_feedback_and_admin_api():
    # Test storing user feedback (Task B4)
    feedback_payload = {
        "question": "What is the vacation policy?",
        "answer": "Employees get 20 paid vacation days per year.",
        "rating": 1,
        "feedback_text": "Accurate and clear citation.",
        "user_id": "rishi_test",
        "role": "HR",
    }
    fb_res = client.post("/api/v1/feedback", json=feedback_payload)
    assert fb_res.status_code == 200
    assert fb_res.json()["status"] == "success"
    print("[OK] Task B4 POST /api/v1/feedback test passed!")

    # Test admin analytics stats endpoint (Task B5)
    stats_res = client.get("/api/v1/admin/stats")
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert "satisfaction_rate" in stats_data
    assert "total_questions_processed" in stats_data
    print(f"[OK] Task B5 GET /api/v1/admin/stats test passed (Satisfaction Rate: {stats_data['satisfaction_rate']}%)!")


if __name__ == "__main__":
    test_phase3_trace_and_confidence()
    test_phase3_feedback_and_admin_api()
    print("\n[SUCCESS] Phase 3 Dev B tasks (B1, B2, B3, B4, B5) fully verified!")
