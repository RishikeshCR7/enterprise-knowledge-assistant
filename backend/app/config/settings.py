import os
from typing import Optional
from pydantic_settings import BaseSettings

# Absolute path to repository root directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class Settings(BaseSettings):
    PROJECT_NAME: str = "Enterprise Knowledge Assistant"
    # Ensure CHROMA_PERSIST_DIR uses absolute path regardless of current working directory
    CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", os.path.join(BASE_DIR, "chroma_db"))
    COLLECTION_NAME: str = os.getenv("COLLECTION_NAME", "enterprise_documents")
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150

    # LangSmith Observability Tracing Settings (Task A4)
    LANGCHAIN_TRACING_V2: str = os.getenv("LANGCHAIN_TRACING_V2", "false")
    LANGCHAIN_ENDPOINT: str = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
    LANGCHAIN_API_KEY: Optional[str] = os.getenv("LANGCHAIN_API_KEY", None)
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "enterprise-knowledge-assistant")

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
