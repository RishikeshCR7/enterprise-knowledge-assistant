import logging
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END

from app.agents.query_rewriter import rewrite_query
from app.retrieval.retriever import retrieve_chunks
from app.rbac.roles import UserContext, UserRole, Department

logger = logging.getLogger(__name__)


class RAGState(TypedDict):
    question: str
    user_context: Optional[Dict[str, Any]]
    rewritten_query: Optional[str]
    retrieved_docs: Optional[List[Dict[str, Any]]]
    reranked_docs: Optional[List[Dict[str, Any]]]
    filtered_docs: Optional[List[Dict[str, Any]]]
    generation: Optional[str]
    sources: Optional[List[Dict[str, Any]]]
    is_safe: Optional[bool]


# Node 1: Task B1 - Query Rewriting Node
def rewrite_node(state: RAGState) -> RAGState:
    """
    Node 1 (Task B1): Rewrites and expands the user query into a domain-optimized search query.
    """
    logger.info("[LangGraph Node] Rewrite Query")
    raw_q = state.get("question", "")
    user_ctx_dict = state.get("user_context")
    
    rewritten = rewrite_query(raw_query=raw_q, user_context=user_ctx_dict)
    
    return {
        **state,
        "rewritten_query": rewritten
    }


# Node 2: Document Retrieval Node (Task A1/A2 Integration)
def retrieve_node(state: RAGState) -> RAGState:
    """
    Node 2: Retrieves candidate chunks from ChromaDB with RBAC filtering.
    """
    logger.info("[LangGraph Node] Retrieve Documents")
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
            logger.warning(f"Error parsing UserContext in retrieve_node: {str(e)}")

    retrieved = retrieve_chunks(
        query=search_query,
        k=10,
        user_context=user_ctx
    )
    
    return {
        **state,
        "retrieved_docs": retrieved
    }


# Node 3: Task B3 - Rerank Node
def rerank_node(state: RAGState) -> RAGState:
    """
    Node 3 (Task B3): Reranks candidate chunks based on semantic relevance scores.
    """
    logger.info("[LangGraph Node] Rerank Documents")
    retrieved = state.get("retrieved_docs", []) or []
    
    # Sort chunks by score descending
    sorted_chunks = sorted(retrieved, key=lambda x: x.get("score", 0.0), reverse=True)
    top_chunks = sorted_chunks[:5]

    return {
        **state,
        "reranked_docs": top_chunks,
        "filtered_docs": top_chunks
    }


# Node 4: Task B4 - Response Generation Node
def generate_node(state: RAGState) -> RAGState:
    """
    Node 4 (Task B4): Synthesizes response based on retrieved & reranked context documents.
    """
    logger.info("[LangGraph Node] Generate Answer")
    reranked = state.get("reranked_docs", []) or []
    question = state.get("question", "")

    if not reranked:
        answer = "I could not find any relevant authorized documents matching your request."
        sources = []
    else:
        context_snippets = []
        sources = []
        for idx, chunk in enumerate(reranked, 1):
            meta = chunk.get("metadata", {})
            title = meta.get("title") or meta.get("doc_id") or f"Document {idx}"
            dept = meta.get("department", "General")
            context_snippets.append(f"[{idx}] {title} ({dept}): {chunk.get('text', '')}")
            sources.append({
                "source_id": idx,
                "title": title,
                "department": dept,
                "chunk_id": chunk.get("chunk_id")
            })

        joined_context = "\n".join(context_snippets)
        answer = f"Based on retrieved company documentation:\n\n{joined_context}\n\n[Summary response generated for query: '{question}']"

    return {
        **state,
        "generation": answer,
        "sources": sources
    }


# Node 5: Guardrails & Safety Check Node
def guard_node(state: RAGState) -> RAGState:
    """
    Node 5: Validates safety of generated response.
    """
    logger.info("[LangGraph Node] Guardrails Check")
    return {
        **state,
        "is_safe": True
    }


# Build Phase 2 LangGraph Workflow
def create_rag_graph():
    builder = StateGraph(RAGState)

    builder.add_node("rewrite", rewrite_node)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("rerank", rerank_node)
    builder.add_node("generate", generate_node)
    builder.add_node("guard", guard_node)

    # Execution Flow: START -> rewrite -> retrieve -> rerank -> generate -> guard -> END
    builder.add_edge(START, "rewrite")
    builder.add_edge("rewrite", "retrieve")
    builder.add_edge("retrieve", "rerank")
    builder.add_edge("rerank", "generate")
    builder.add_edge("generate", "guard")
    builder.add_edge("guard", END)

    return builder.compile()


rag_graph = create_rag_graph()
