import pytest
from app.retrieval.hybrid_search import BM25Indexer, HybridRetriever, hybrid_retriever
from app.database.chroma_store import chroma_store
from app.models.document import DocumentMetadata, DocumentChunk
from app.rbac.roles import UserContext, UserRole, Department


@pytest.fixture(scope="module")
def setup_hybrid_documents():
    eng_meta = DocumentMetadata(
        doc_id="doc_hybrid_eng",
        title="Docker Container Deployment Guide",
        department="Engineering",
        security_level="Internal",
        allowed_roles=["Engineering", "Executive"],
        owner="DevOps Team",
        file_type="pdf"
    )

    fin_meta = DocumentMetadata(
        doc_id="doc_hybrid_fin",
        title="Corporate Travel Per Diem Expense Policy",
        department="Finance",
        security_level="Confidential",
        allowed_roles=["Finance", "Executive"],
        owner="Finance Team",
        file_type="pdf"
    )

    chunk1 = DocumentChunk(
        chunk_id="doc_hybrid_eng_chunk_0",
        doc_id="doc_hybrid_eng",
        text="Docker images must be scanned for security vulnerabilities using Trivy prior to push.",
        chunk_index=0,
        metadata=eng_meta
    )

    chunk2 = DocumentChunk(
        chunk_id="doc_hybrid_fin_chunk_0",
        doc_id="doc_hybrid_fin",
        text="Per diem meal allowance for corporate travel is capped at $75 per day with itemized receipts.",
        chunk_index=0,
        metadata=fin_meta
    )

    chroma_store.add_documents([chunk1, chunk2])
    hybrid_retriever.bm25_indexer.build_index(force_refresh=True)
    return {"eng_id": "doc_hybrid_eng", "fin_id": "doc_hybrid_fin"}


def test_bm25_search(setup_hybrid_documents):
    bm25 = BM25Indexer()
    bm25.build_index(force_refresh=True)
    results = bm25.search("Docker Trivy", k=5)
    assert len(results) >= 1
    assert any("Docker" in r["text"] or "Trivy" in r["text"] for r in results)


def test_hybrid_rrf_fusion(setup_hybrid_documents):
    vec_results = [
        {"chunk_id": "c1", "text": "sample text 1", "metadata": {"doc_id": "d1"}},
        {"chunk_id": "c2", "text": "sample text 2", "metadata": {"doc_id": "d2"}}
    ]
    bm25_results = [
        {"chunk_id": "c2", "text": "sample text 2", "metadata": {"doc_id": "d2"}},
        {"chunk_id": "c3", "text": "sample text 3", "metadata": {"doc_id": "d3"}}
    ]

    retriever = HybridRetriever()
    fused = retriever.reciprocal_rank_fusion(vec_results, bm25_results, rrf_k=60, top_k=3)
    assert len(fused) == 3
    # c2 was present in both top 2, so it should rank first by RRF score
    assert fused[0]["chunk_id"] == "c2"


def test_hybrid_search_with_rbac(setup_hybrid_documents):
    fin_user = UserContext(
        user_id="fin_user_01",
        username="FinanceUser",
        role=UserRole.FINANCE,
        department=Department.FINANCE
    )

    results = hybrid_retriever.search("per diem travel expense allowance $75", k=3, user_context=fin_user)
    assert len(results) >= 1
    assert any("per diem" in r["text"].lower() or r["chunk_id"] == "doc_hybrid_fin_chunk_0" for r in results)
