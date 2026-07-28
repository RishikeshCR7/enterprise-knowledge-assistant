from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    doc_id: str = Field(..., description="Unique document ID (UUID or slug)")
    title: str = Field(..., description="Title of the document")
    department: str = Field(..., description="Owning department (e.g. HR, Engineering, Finance, Legal, Sales)")
    security_level: str = Field(default="Internal", description="Security clearance required (Public, Internal, Confidential, Restricted)")
    allowed_roles: List[str] = Field(default_factory=list, description="Roles permitted to view this document")
    owner: str = Field(default="System", description="Owner or team responsible")
    created_date: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="ISO timestamp when created")
    last_modified: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="ISO timestamp when updated")
    file_type: str = Field(..., description="File extension or mime format (pdf, docx, xlsx, txt)")

    def to_chroma_metadata(self) -> Dict[str, Any]:
        """
        Converts metadata to a dictionary compatible with ChromaDB.
        ChromaDB supports primitive types (str, int, float, bool) and lists of str.
        We provide 'allowed_roles_str' as comma-separated as well for standard string filtering.
        """
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "department": self.department,
            "security_level": self.security_level,
            "allowed_roles": self.allowed_roles,
            "allowed_roles_str": ",".join(self.allowed_roles),
            "owner": self.owner,
            "created_date": self.created_date,
            "last_modified": self.last_modified,
            "file_type": self.file_type,
        }

    @classmethod
    def from_chroma_metadata(cls, meta: Dict[str, Any]) -> "DocumentMetadata":
        allowed_roles = meta.get("allowed_roles")
        if isinstance(allowed_roles, str):
            allowed_roles = [r.strip() for r in allowed_roles.split(",") if r.strip()]
        elif not allowed_roles:
            allowed_roles = []
            
        return cls(
            doc_id=meta.get("doc_id", ""),
            title=meta.get("title", ""),
            department=meta.get("department", "General"),
            security_level=meta.get("security_level", "Internal"),
            allowed_roles=allowed_roles,
            owner=meta.get("owner", "System"),
            created_date=meta.get("created_date", ""),
            last_modified=meta.get("last_modified", ""),
            file_type=meta.get("file_type", "txt")
        )


class DocumentChunk(BaseModel):
    chunk_id: str = Field(..., description="Unique chunk identifier, e.g. {doc_id}_chunk_0")
    doc_id: str = Field(..., description="Parent document identifier")
    text: str = Field(..., description="Text content of the chunk")
    chunk_index: int = Field(..., description="Index sequence number of the chunk")
    metadata: DocumentMetadata = Field(..., description="Metadata of the document")
    embedding: Optional[List[float]] = Field(default=None, description="384-dim dense vector embedding")


class UploadDocumentResponse(BaseModel):
    doc_id: str
    chunk_count: int
    metadata: DocumentMetadata
    message: str = "Document uploaded and indexed successfully"


class DocumentListResponse(BaseModel):
    documents: List[DocumentMetadata]
    total: int
