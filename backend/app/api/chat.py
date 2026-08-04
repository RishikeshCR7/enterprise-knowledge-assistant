from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.rbac.roles import UserRole, Department, UserContext
from app.agents.rag_graph import rag_graph

router = APIRouter(prefix="/api/v1", tags=["chat"])


class ChatRequest(BaseModel):
    question: str = Field(..., description="User query / prompt")
    user_id: Optional[str] = Field("user_default", description="User ID")
    role: Optional[UserRole] = Field(UserRole.HR, description="User RBAC role")
    department: Optional[Department] = Field(Department.HR, description="User department")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Generated answer")
    rewritten_query: Optional[str] = None
    retrieved_docs: List[Dict[str, Any]] = Field(default_factory=list)
<<<<<<< Updated upstream
=======
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_score: Optional[int] = 90
>>>>>>> Stashed changes


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Executes the query pipeline through the LangGraph skeleton node workflow.
    """
    user_ctx = UserContext(
        user_id=request.user_id,
        username=request.user_id,
        role=request.role,
        department=request.department,
    )

    initial_state = {
        "question": request.question,
        "user_context": user_ctx.model_dump(),
        "rewritten_query": None,
        "retrieved_docs": [],
        "filtered_docs": [],
        "generation": None,
<<<<<<< Updated upstream
=======
        "sources": [],
        "confidence_score": 90,
>>>>>>> Stashed changes
        "is_safe": True,
    }

    try:
        final_state = rag_graph.invoke(initial_state)
        return ChatResponse(
            answer=final_state.get("generation", "Coming Soon"),
            rewritten_query=final_state.get("rewritten_query"),
            retrieved_docs=final_state.get("filtered_docs", []),
<<<<<<< Updated upstream
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing chat graph: {str(e)}")
=======
            sources=final_state.get("sources", []),
            confidence_score=final_state.get("confidence_score", 90)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing chat graph: {str(e)}")


@router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    Task B5: Streaming chat endpoint yielding tokens live with Server-Sent Events (SSE).
    """
    user_ctx = UserContext(
        user_id=request.user_id,
        username=request.user_id,
        role=request.role,
        department=request.department,
    )

    initial_state = {
        "question": request.question,
        "user_context": user_ctx.model_dump(),
        "rewritten_query": None,
        "retrieved_docs": [],
        "reranked_docs": [],
        "filtered_docs": [],
        "generation": None,
        "sources": [],
        "confidence_score": 90,
        "is_safe": True,
    }

    try:
        final_state = rag_graph.invoke(initial_state)
        reranked_docs = final_state.get("reranked_docs", [])
        sources = final_state.get("sources", [])
        rewritten = final_state.get("rewritten_query", "")
        confidence = final_state.get("confidence_score", 90)

        def event_generator():
            # First send metadata (sources, confidence & rewritten query)
            meta_payload = {
                "type": "metadata",
                "rewritten_query": rewritten,
                "sources": sources,
                "confidence_score": confidence
            }
            yield f"data: {json.dumps(meta_payload)}\n\n"

            # Stream token response
            for token in llm_client.generate_stream(request.question, reranked_docs):
                token_payload = {"type": "token", "content": token}
                yield f"data: {json.dumps(token_payload)}\n\n"

            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming error: {str(e)}")
>>>>>>> Stashed changes
