from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END


class RAGState(TypedDict):
    question: str
    user_context: Optional[Dict[str, Any]]
    rewritten_query: Optional[str]
    retrieved_docs: Optional[List[Dict[str, Any]]]
    filtered_docs: Optional[List[Dict[str, Any]]]
    generation: Optional[str]
    is_safe: Optional[bool]


# Graph Nodes (Skeleton / Mocks)
def rewrite_node(state: RAGState) -> RAGState:
    """Node 1: Query rewriting/expansion."""
    print("[LangGraph Node] Rewrite")
    return {
        **state,
        "rewritten_query": f"Optimized: {state['question']}"
    }


def retrieve_node(state: RAGState) -> RAGState:
    """Node 2: Document retrieval from vector database."""
    print("[LangGraph Node] Retrieve")
    return {
        **state,
        "retrieved_docs": [
            {"id": "doc_1", "content": "Sample HR policy document", "score": 0.95}
        ]
    }


def filter_node(state: RAGState) -> RAGState:
    """Node 3: RBAC & relevance filtering."""
    print("[LangGraph Node] Filter (RBAC)")
    return {
        **state,
        "filtered_docs": state.get("retrieved_docs", [])
    }


def generate_node(state: RAGState) -> RAGState:
    """Node 4: Response generation."""
    print("[LangGraph Node] Generate")
    return {
        **state,
        "generation": "Coming Soon - Hello Enterprise AI"
    }


def guard_node(state: RAGState) -> RAGState:
    """Node 5: Guardrails and safety check."""
    print("[LangGraph Node] Guard")
    return {
        **state,
        "is_safe": True
    }


# Build LangGraph Skeleton Graph
def create_rag_graph():
    builder = StateGraph(RAGState)

    builder.add_node("rewrite", rewrite_node)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("filter", filter_node)
    builder.add_node("generate", generate_node)
    builder.add_node("guard", guard_node)

    # Define linear execution pipeline: Rewrite -> Retrieve -> Filter -> Generate -> Guard
    builder.add_edge(START, "rewrite")
    builder.add_edge("rewrite", "retrieve")
    builder.add_edge("retrieve", "filter")
    builder.add_edge("filter", "generate")
    builder.add_edge("generate", "guard")
    builder.add_edge("guard", END)

    return builder.compile()


rag_graph = create_rag_graph()
