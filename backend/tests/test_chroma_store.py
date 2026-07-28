import pytest
from app.database.chroma_store import ChromaStore
from app.models.document import DocumentMetadata, DocumentChunk


def test_chroma_store_operations(tmp_path):
    store = ChromaStore(persist_dir=str(tmp_path / "chroma_test"), collection_name="test_collection")

    doc_meta = DocumentMetadata(
        doc_id="doc_100",
        title="Engineering API Standards",
        department="Engineering",
        security_level="Internal",
        allowed_roles=["Engineering", "Executive"],
        owner="Tech Lead",
        file_type="pdf"
    )

    chunk1 = DocumentChunk(
        chunk_id="doc_100_chunk_0",
        doc_id="doc_100",
        text="All REST endpoints must be versioned under /api/v1 prefix.",
        chunk_index=0,
        metadata=doc_meta
    )

    # 1. Add document chunks
    added_count = store.add_documents([chunk1])
    assert added_count == 1

    # 2. Similarity search
    results = store.similarity_search("REST API endpoints", k=2)
    assert len(results) >= 1
    assert results[0]["chunk_id"] == "doc_100_chunk_0"

    # 3. List documents
    docs = store.list_documents()
    assert len(docs) == 1
    assert docs[0].doc_id == "doc_100"

    # 4. Delete document
    deleted = store.delete_document("doc_100")
    assert deleted is True
    assert len(store.list_documents()) == 0
