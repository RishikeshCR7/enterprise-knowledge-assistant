import uuid
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status

from app.models.document import DocumentMetadata, UploadDocumentResponse, DocumentListResponse
from app.ingestion.parser import DocumentParser
from app.ingestion.chunker import chunker
from app.database.embeddings import embedding_pipeline
from app.database.chroma_store import chroma_store

router = APIRouter(prefix="/api/v1/documents", tags=["Documents Ingestion"])


@router.post("/upload", response_model=UploadDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    department: str = Form("General"),
    security_level: str = Form("Internal"),
    allowed_roles: Optional[str] = Form(None),
    owner: str = Form("System Owner"),
):
    """
    Accepts PDF, DOCX, XLSX file upload.
    Parses -> Chunks -> Embeds -> Stores in ChromaDB -> Returns success response.
    """
    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        doc_id = str(uuid.uuid4())
        doc_title = title if title and title.strip() else file.filename
        file_ext = file.filename.split(".")[-1].lower() if file.filename else "pdf"

        # Parse allowed_roles string (comma separated) into list
        roles_list = []
        if allowed_roles:
            roles_list = [r.strip() for r in allowed_roles.split(",") if r.strip()]
        if not roles_list:
            roles_list = [department, "Executive"]

        # Step 1: Parse document
        raw_text, parse_meta = DocumentParser.parse_file(file.filename, file_bytes)

        # Step 2: Construct metadata
        doc_metadata = DocumentMetadata(
            doc_id=doc_id,
            title=doc_title,
            department=department,
            security_level=security_level,
            allowed_roles=roles_list,
            owner=owner,
            file_type=file_ext
        )

        # Step 3: Chunk document
        chunks = chunker.chunk_document(doc_id, raw_text, doc_metadata)

        # Step 4: Generate Embeddings
        chunk_texts = [c.text for c in chunks]
        embeddings = embedding_pipeline.embed_documents(chunk_texts)
        for idx, emb in enumerate(embeddings):
            chunks[idx].embedding = emb

        # Step 5: Store in ChromaDB
        chroma_store.add_documents(chunks)

        return UploadDocumentResponse(
            doc_id=doc_id,
            chunk_count=len(chunks),
            metadata=doc_metadata,
            message="Document parsed, chunked, embedded, and stored in ChromaDB successfully"
        )

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document upload: {str(e)}")


@router.get("", response_model=DocumentListResponse)
async def list_documents():
    """
    Lists all indexed documents currently stored in ChromaDB.
    """
    docs = chroma_store.list_documents()
    return DocumentListResponse(documents=docs, total=len(docs))


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """
    Deletes all chunks of a document from ChromaDB vector store.
    """
    success = chroma_store.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Document with ID '{doc_id}' not found or deletion failed.")
    return {"message": f"Document {doc_id} deleted successfully."}
