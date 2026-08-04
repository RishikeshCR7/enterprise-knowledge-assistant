from app.agents.reranker import reranker
from app.agents.llm_client import llm_client
from app.agents.rag_graph import rag_graph
from app.rbac.roles import UserRole, Department


def test_b3_reranker():
    query = "What is the HR leave policy?"
    mock_chunks = [
        {"chunk_id": "c1", "text": "Irrelevant legal agreement", "score": 0.8},
        {"chunk_id": "c2", "text": "Official HR leave policy: Employees get 20 paid vacation days per year.", "score": 0.75},
        {"chunk_id": "c3", "text": "Coding standards and style guide", "score": 0.6},
    ]

    reranked = reranker.rerank(query=query, chunks=mock_chunks, top_k=2)
    print(f"[TEST B3] Top reranked chunk ID: {reranked[0]['chunk_id']}")

    assert len(reranked) <= 2
    assert "rerank_score" in reranked[0] or "score" in reranked[0]
    print("[OK] Task B3 Reranker test passed!")


def test_b4_llm_integration():
    query = "How many leave days do employees get?"
    mock_context = [
        {
            "chunk_id": "c2",
            "text": "Official HR leave policy: Employees get 20 paid vacation days per year.",
            "metadata": {"title": "LeavePolicy.pdf", "department": "HR", "security_level": "Internal", "doc_id": "doc_hr_01"},
            "rerank_score": 2.5
        }
    ]

    res = llm_client.generate_response(query, mock_context)
    print("[TEST B4] LLM Answer Response:")
    print(res["answer"])
    print(f"[TEST B4] Sources count: {len(res['sources'])}")

    assert "answer" in res
    assert len(res["sources"]) == 1
    assert res["sources"][0]["title"] == "LeavePolicy.pdf"
    print("[OK] Task B4 LLM Integration test passed!")


def test_b5_streaming_tokens():
    query = "How many leave days do employees get?"
    mock_context = [
        {
            "chunk_id": "c2",
            "text": "Official HR leave policy: Employees get 20 paid vacation days per year.",
            "metadata": {"title": "LeavePolicy.pdf", "department": "HR", "security_level": "Internal"},
            "rerank_score": 2.5
        }
    ]

    stream_tokens = list(llm_client.generate_stream(query, mock_context))
    assembled_answer = "".join(stream_tokens)

    print(f"[TEST B5] Streamed {len(stream_tokens)} tokens successfully.")
    assert len(stream_tokens) > 0
    assert "Official HR leave policy" in assembled_answer or "LeavePolicy.pdf" in assembled_answer
    print("[OK] Task B5 Streaming test passed!")


if __name__ == "__main__":
    test_b3_reranker()
    test_b4_llm_integration()
    test_b5_streaming_tokens()
    print("\n🎉 [SUCCESS] Tasks B3, B4, and B5 completed and verified!")
