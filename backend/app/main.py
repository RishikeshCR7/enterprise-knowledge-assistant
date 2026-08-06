from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.retrieval import router as retrieval_router
from app.api.analytics import router as analytics_router
from app.api.feedback import router as feedback_router

app = FastAPI(
    title="Enterprise Knowledge Assistant API",
    description="RAG System with RBAC and Multi-Agent Orchestration",
    version="0.1.0",
)

# Enable CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(retrieval_router)
app.include_router(analytics_router)
app.include_router(feedback_router)


@app.get("/")
async def root():
    return {"message": "Hello Enterprise AI"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
