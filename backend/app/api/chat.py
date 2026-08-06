import json
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.rbac.roles import UserRole, Department, UserContext
from app.agents.rag_graph import rag_graph
from app.agents.llm_client import llm_client

router = APIRouter(prefix="/api/v1", tags=["chat"])


class ChatMessageTurn(BaseModel):
    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="message content")


class ChatRequest(BaseModel):
    question: str = Field(..., description="User query / prompt")
    user_id: Optional[str] = Field("user_default", description="User ID")
    role: Optional[UserRole] = Field(UserRole.HR, description="User RBAC role")
    department: Optional[Department] = Field(Department.HR, description="User department")
    chat_history: Optional[List[ChatMessageTurn]] = Field(default_factory=list, description="Conversation memory")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Generated answer")
    rewritten_query: Optional[str] = None
    retrieved_docs: List[Dict[str, Any]] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_score: int = Field(90, description="Overall confidence percentage")
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list, description="Multi-Agent trace telemetry")


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Standard synchronous chat endpoint executing full LangGraph workflow.
    """
    user_ctx = UserContext(
        user_id=request.user_id,
        username=request.user_id,
        role=request.role,
        department=request.department,
    )

    history_dicts = [h.model_dump() for h in request.chat_history] if request.chat_history else []

    initial_state = {
        "question": request.question,
        "user_context": user_ctx.model_dump(),
        "chat_history": history_dicts,
        "rewritten_query": None,
        "retrieved_docs": [],
        "reranked_docs": [],
        "filtered_docs": [],
        "generation": None,
        "sources": [],
        "confidence_score": 0,
        "execution_trace": [],
        "is_safe": True,
    }

    try:
        final_state = rag_graph.invoke(initial_state)
        return ChatResponse(
            answer=final_state.get("generation", "No response generated"),
            rewritten_query=final_state.get("rewritten_query"),
            retrieved_docs=final_state.get("filtered_docs", []),
            sources=final_state.get("sources", []),
            confidence_score=final_state.get("confidence_score", 90),
            execution_trace=final_state.get("execution_trace", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing chat graph: {str(e)}")


@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Task B5 & Integration 4: Streaming chat endpoint with live trace events and token stream via SSE.
    """
    user_ctx = UserContext(
        user_id=request.user_id,
        username=request.user_id,
        role=request.role,
        department=request.department,
    )

    history_dicts = [h.model_dump() for h in request.chat_history] if request.chat_history else []

    initial_state = {
        "question": request.question,
        "user_context": user_ctx.model_dump(),
        "chat_history": history_dicts,
        "rewritten_query": None,
        "retrieved_docs": [],
        "reranked_docs": [],
        "filtered_docs": [],
        "generation": None,
        "sources": [],
        "confidence_score": 0,
        "execution_trace": [],
        "is_safe": True,
    }

    try:
        final_state = rag_graph.invoke(initial_state)
        reranked_docs = final_state.get("reranked_docs", [])
        sources = final_state.get("sources", [])
        rewritten = final_state.get("rewritten_query", "")
        confidence = final_state.get("confidence_score", 90)
        traces = final_state.get("execution_trace", [])

        def event_generator():
            # 1. Send trace events live (Task B1 Multi-Agent Trace Viewer)
            for tr in traces:
                trace_payload = {"type": "trace", "data": tr}
                yield f"data: {json.dumps(trace_payload)}\n\n"

            # 2. Send metadata payload (sources, rewritten query, confidence score)
            meta_payload = {
                "type": "metadata",
                "rewritten_query": rewritten,
                "sources": sources,
                "confidence_score": confidence
            }
            yield f"data: {json.dumps(meta_payload)}\n\n"

            # 3. Stream LLM tokens live
            for token in llm_client.generate_stream(request.question, reranked_docs, user_context=user_ctx.model_dump()):
                token_payload = {"type": "token", "content": token}
                yield f"data: {json.dumps(token_payload)}\n\n"

            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming error: {str(e)}")
