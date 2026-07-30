from app.agents.query_rewriter import rewrite_query
from app.agents.rag_graph import rag_graph
from app.rbac.roles import UserRole, Department


def test_query_rewriter():
    user_context = {"department": "HR", "role": "HR"}
    raw_query = "Vacation policy?"

    rewritten = rewrite_query(raw_query, user_context)
    print(f"[TEST B1] Raw: '{raw_query}' -> Rewritten: '{rewritten}'")

    assert "Vacation policy?" in rewritten
    assert "official HR leave policy" in rewritten
    assert "[HR Department]" in rewritten
    print("[OK] Task B1 query_rewriter test passed!")


def test_langgraph_workflow():
    initial_state = {
        "question": "What is the vacation policy?",
        "user_context": {
            "user_id": "test_user_01",
            "username": "rishi",
            "role": UserRole.HR.value,
            "department": Department.HR.value,
        },
        "rewritten_query": None,
        "retrieved_docs": None,
        "reranked_docs": None,
        "filtered_docs": None,
        "generation": None,
        "sources": None,
        "is_safe": None,
    }

    final_state = rag_graph.invoke(initial_state)

    print("[TEST B2] LangGraph Execution Output:")
    print(f"  Rewritten Query: {final_state.get('rewritten_query')}")
    print(f"  Retrieved Chunks: {len(final_state.get('retrieved_docs') or [])}")
    print(f"  Reranked Chunks: {len(final_state.get('reranked_docs') or [])}")
    print(f"  Generation: {final_state.get('generation')[:60]}...")
    print(f"  Is Safe: {final_state.get('is_safe')}")

    assert final_state.get("rewritten_query") is not None
    assert final_state.get("is_safe") is True
    print("[OK] Task B2 langgraph_workflow test passed!")


if __name__ == "__main__":
    test_query_rewriter()
    test_langgraph_workflow()
    print("[OK] All Task B1 & Task B2 tests completed successfully!")
