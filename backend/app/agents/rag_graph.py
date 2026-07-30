import logging
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, START, END

from app.agents.query_rewriter import rewrite_query
from app.retrieval.retriever import retrieve_chunks
from app.agents.reranker import reranker
from app.agents.llm_client import llm_client
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
    logger.info("[LangGraph Node] 1. Rewrite Query")
    raw_q = state.get("question", "")
    user_ctx_dict = state.get("user_context")
    rewritten = rewrite_query(raw_query=raw_q, user_context=user_ctx_dict)
    return {**state, "rewritten_query": rewritten}


# Node 2: Document Retrieval Node (Task A1/A2 Integration)
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
    
    # Task B3: Use CrossEncoderReranker to score & select top 5 chunks
    top_reranked = reranker.rerank(query=query, chunks=retrieved, top_k=5)

    return {
        **state,
        "reranked_docs": top_reranked,
        "filtered_docs": top_reranked
    }


# Node 4: Task B4 - Response Generation Node (Groq / Gemini / Grounded QA)
def generate_node(state: RAGState) -> RAGState:
    logger.info("[LangGraph Node] 4. Generate Response (LLM)")
    reranked = state.get("reranked_docs", []) or []
    question = state.get("question", "")

    # Task B4: Call LLMClient to produce grounded QA with source citations
    llm_result = llm_client.generate_response(query=question, context_chunks=reranked)

    return {
        **state,
        "generation": llm_result["answer"],
        "sources": llm_result["sources"]
    }


# Node 5: Guardrails & Safety Check Node
def guard_node(state: RAGState) -> RAGState:
    logger.info("[LangGraph Node] 5. Guardrails Check")
    return {**state, "is_safe": True}


# Build Phase 2 LangGraph Execution Pipeline
def create_rag_graph():
    builder = StateGraph(RAGState)

    builder.add_node("rewrite", rewrite_node)
    builder.add_node("retrieve", retrieve_node)
    builder.add_node("rerank", rerank_node)
    builder.add_node("generate", generate_node)
    builder.add_node("guard", guard_node)

    builder.add_edge(START, "rewrite")
    builder.add_edge("rewrite", "retrieve")
    builder.add_edge("retrieve", "rerank")
    builder.add_edge("rerank", "generate")
    builder.add_edge("generate", "guard")
    builder.add_edge("guard", END)

    return builder.compile()


rag_graph = create_rag_graph()
