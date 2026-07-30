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
    sources: List[Dict[str, Any]] = Field(default_factory=list)


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
        "is_safe": True,
    }

    try:
        final_state = rag_graph.invoke(initial_state)
        return ChatResponse(
            answer=final_state.get("generation", "Coming Soon"),
            rewritten_query=final_state.get("rewritten_query"),
            retrieved_docs=final_state.get("filtered_docs", []),
            sources=final_state.get("sources", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing chat graph: {str(e)}")
