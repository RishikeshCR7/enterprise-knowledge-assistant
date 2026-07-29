from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.retrieval.retriever import retrieve_chunks, retrieve_documents, retrieve_with_filters
from app.rbac.roles import UserContext, UserRole, Department, SecurityLevel

router = APIRouter(prefix="/api/v1/retrieval", tags=["Candidate Retrieval API"])


class RetrievalSearchRequest(BaseModel):
    query: str = Field(..., description="User search query")
    department: Optional[str] = Field(None, description="Department filter (HR, Engineering, Finance, Legal, Sales)")
    security_level: Optional[str] = Field(None, description="Security clearance filter")
    user_id: Optional[str] = Field("user_01", description="User ID for RBAC clearance")
    username: Optional[str] = Field("TestUser", description="Username")
    role: Optional[UserRole] = Field(None, description="User role (e.g. Engineering, HR, Executive)")
    user_department: Optional[Department] = Field(None, description="User primary department")
    k: int = Field(4, description="Top k candidates to return")


class RetrievalSearchResponse(BaseModel):
    query: str
    candidate_count: int
    results: List[Dict[str, Any]]


@router.post("/search", response_model=RetrievalSearchResponse)
async def search_candidate_chunks(request: RetrievalSearchRequest):
    """
    Task A2: Endpoint to retrieve candidate chunks with metadata and RBAC filtering.
    Does NOT call LLM. Returns vector search candidate chunks.
    """
    try:
        user_ctx = None
        if request.role and request.user_department:
            user_ctx = UserContext(
                user_id=request.user_id or "user_01",
                username=request.username or "TestUser",
                role=request.role,
                department=request.user_department
            )

        chunks = retrieve_with_filters(
            query=request.query,
            department=request.department,
            security_level=request.security_level,
            user_context=user_ctx,
            k=request.k
        )

        return RetrievalSearchResponse(
            query=request.query,
            candidate_count=len(chunks),
            results=chunks
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval search error: {str(e)}")


@router.post("/documents", response_model=RetrievalSearchResponse)
async def search_candidate_documents(request: RetrievalSearchRequest):
    """
    Task A2: Endpoint to retrieve candidate distinct documents with metadata and RBAC filtering.
    """
    try:
        user_ctx = None
        if request.role and request.user_department:
            user_ctx = UserContext(
                user_id=request.user_id or "user_01",
                username=request.username or "TestUser",
                role=request.role,
                department=request.user_department
            )

        docs = retrieve_documents(
            query=request.query,
            k=request.k,
            user_context=user_ctx
        )

        return RetrievalSearchResponse(
            query=request.query,
            candidate_count=len(docs),
            results=docs
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval documents search error: {str(e)}")
