from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END

<<<<<<< Updated upstream
=======
from app.agents.query_rewriter import rewrite_query, classify_intent
from app.retrieval.retriever import retrieve_chunks
from app.agents.reranker import reranker, compute_confidence_score, deduplicate_sources
from app.agents.llm_client import llm_client
from app.rbac.roles import UserContext, UserRole, Department

logger = logging.getLogger(__name__)

>>>>>>> Stashed changes

class RAGState(TypedDict):
    question: str
    user_context: Optional[Dict[str, Any]]
    rewritten_query: Optional[str]
    retrieved_docs: Optional[List[Dict[str, Any]]]
    filtered_docs: Optional[List[Dict[str, Any]]]
    generation: Optional[str]
<<<<<<< Updated upstream
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
=======
    sources: Optional[List[Dict[str, Any]]]
    confidence_score: Optional[int]
    is_safe: Optional[bool]


# Node 1: Task B1 - Query Rewriting Node & Intent Router
def rewrite_node(state: RAGState) -> RAGState:
    logger.info("[LangGraph Node] 1. Rewrite Query")
    raw_q = state.get("question", "")
    user_ctx_dict = state.get("user_context")

    intent = classify_intent(raw_q)
    if intent == "GREETING":
        return {
            **state,
            "rewritten_query": raw_q,
            "retrieved_docs": [],
            "reranked_docs": [],
            "filtered_docs": [],
            "generation": "Hello! How can I help you today? Feel free to ask any questions regarding company policies, engineering standards, financial guidelines, or legal compliance.",
            "sources": [],
            "confidence_score": 100
        }

    rewritten = rewrite_query(raw_query=raw_q, user_context=user_ctx_dict)
    return {**state, "rewritten_query": rewritten}


# Conditional Edge Router
def route_intent(state: RAGState) -> str:
    raw_q = state.get("question", "")
    if classify_intent(raw_q) == "GREETING":
        return "guard"
    return "retrieve"


# Node 2: Document Retrieval Node
def retrieve_node(state: RAGState) -> RAGState:
    logger.info("[LangGraph Node] 2. Retrieve Documents")
    search_query = state.get("rewritten_query") or state.get("question", "")
    user_ctx_dict = state.get("user_context")
    
    user_ctx: Optional[UserContext] = None
    if user_ctx_dict:
        try:
            user_ctx = UserContext(
                user_id=user_ctx_dict.get("user_id", "user_anon"),
                username=user_ctx_dict.get("username", "anonymous"),
                role=UserRole(user_ctx_dict.get("role", UserRole.HR.value)),
                department=Department(user_ctx_dict.get("department", Department.HR.value))
            )
        except Exception as e:
            logger.warning(f"Error parsing UserContext: {str(e)}")

    retrieved = retrieve_chunks(query=search_query, k=10, user_context=user_ctx)
    return {**state, "retrieved_docs": retrieved}


# Node 3: Task B3 - Cross-Encoder Rerank Node
def rerank_node(state: RAGState) -> RAGState:
    logger.info("[LangGraph Node] 3. Cross-Encoder Rerank")
    retrieved = state.get("retrieved_docs", []) or []
    query = state.get("rewritten_query") or state.get("question", "")
    
    top_reranked = reranker.rerank(query=query, chunks=retrieved, top_k=5)
    confidence = compute_confidence_score(top_reranked)

    return {
        **state,
        "reranked_docs": top_reranked,
        "filtered_docs": top_reranked,
        "confidence_score": confidence
>>>>>>> Stashed changes
    }


def generate_node(state: RAGState) -> RAGState:
<<<<<<< Updated upstream
    """Node 4: Response generation."""
    print("[LangGraph Node] Generate")
    return {
        **state,
        "generation": "Coming Soon - Hello Enterprise AI"
=======
    logger.info("[LangGraph Node] 4. Generate Response (LLM)")
    reranked = state.get("reranked_docs", []) or []
    question = state.get("question", "")

    llm_result = llm_client.generate_response(query=question, context_chunks=reranked)

    return {
        **state,
        "generation": llm_result["answer"],
        "sources": llm_result["sources"],
        "confidence_score": llm_result.get("confidence_score", state.get("confidence_score", 90))
>>>>>>> Stashed changes
    }


def guard_node(state: RAGState) -> RAGState:
    """Node 5: Guardrails and safety check."""
    print("[LangGraph Node] Guard")
    return {
        **state,
        "is_safe": True
    }


<<<<<<< Updated upstream
# Build LangGraph Skeleton Graph
=======
# Build LangGraph Pipeline with Conditional Routing for Greetings
>>>>>>> Stashed changes
def create_rag_graph():
    builder = StateGraph(RAGState)

    builder.add_node("rewrite", rewrite_node)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("filter", filter_node)
    builder.add_node("generate", generate_node)
    builder.add_node("guard", guard_node)

    # Define linear execution pipeline: Rewrite -> Retrieve -> Filter -> Generate -> Guard
    builder.add_edge(START, "rewrite")
<<<<<<< Updated upstream
    builder.add_edge("rewrite", "retrieve")
    builder.add_edge("retrieve", "filter")
    builder.add_edge("filter", "generate")
=======
    builder.add_conditional_edges("rewrite", route_intent, {
        "guard": "guard",
        "retrieve": "retrieve"
    })
    builder.add_edge("retrieve", "rerank")
    builder.add_edge("rerank", "generate")
>>>>>>> Stashed changes
    builder.add_edge("generate", "guard")
    builder.add_edge("guard", END)

    return builder.compile()


rag_graph = create_rag_graph()
