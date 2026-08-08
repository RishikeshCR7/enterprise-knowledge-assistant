from app.agents.query_rewriter import rewrite_query, classify_intent
from app.agents.rag_graph import rag_graph
from app.agents.reranker import deduplicate_sources, compute_confidence_score
from app.rbac.roles import UserRole, Department


def test_intent_classification():
    assert classify_intent("hi") == "GREETING"
    assert classify_intent("hello") == "GREETING"
    assert classify_intent("what are my timings") == "ENTERPRISE_SEARCH"
    assert classify_intent("vacation policy") == "ENTERPRISE_SEARCH"


def test_query_rewriter():
    user_context = {"department": "HR", "role": "HR"}
    raw_query = "what are my timings"

    rewritten = rewrite_query(raw_query, user_context)
    assert "office working hours" in rewritten

    greeting_rewrite = rewrite_query("hi", user_context)
    assert greeting_rewrite == "hi"


def test_source_deduplication():
    chunks = [
        {"text": "c1", "metadata": {"doc_id": "doc1", "title": "HR Policy"}},
        {"text": "c2", "metadata": {"doc_id": "doc1", "title": "HR Policy"}},
        {"text": "c3", "metadata": {"doc_id": "doc2", "title": "Coding Standard"}}
    ]
    unique = deduplicate_sources(chunks)
    assert len(unique) == 2
    assert unique[0]["title"] == "HR Policy"
    assert unique[1]["title"] == "Coding Standard"


def test_greeting_langgraph_workflow():
    initial_state = {
        "question": "hi",
        "user_context": {
            "user_id": "test_user_01",
            "username": "user",
            "role": UserRole.HR.value,
            "department": Department.HR.value,
        },
        "rewritten_query": None,
        "retrieved_docs": None,
        "reranked_docs": None,
        "filtered_docs": None,
        "generation": None,
        "sources": None,
        "confidence_score": None,
        "is_safe": None,
    }

    final_state = rag_graph.invoke(initial_state)
    assert "Hello!" in final_state["generation"] or "help" in final_state["generation"].lower()
    assert len(final_state["sources"]) == 0
    assert final_state["confidence_score"] == 100


def test_low_confidence_refusal_workflow():
    initial_state = {
        "question": "wtf",
        "user_context": {
            "user_id": "test_user_01",
            "username": "user",
            "role": UserRole.HR.value,
            "department": Department.HR.value,
        },
        "rewritten_query": None,
        "retrieved_docs": None,
        "reranked_docs": None,
        "filtered_docs": None,
        "generation": None,
        "sources": None,
        "confidence_score": None,
        "is_safe": None,
    }

    final_state = rag_graph.invoke(initial_state)
    assert "could not find" in final_state["generation"].lower() or "no matching" in final_state["generation"].lower()
    assert len(final_state["sources"]) == 0
