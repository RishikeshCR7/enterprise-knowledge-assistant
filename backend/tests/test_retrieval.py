import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.chroma_store import chroma_store, build_chroma_filter
from app.retrieval.retriever import retrieve_chunks, retrieve_documents, retrieve_with_filters
from app.rbac.roles import UserContext, UserRole, Department, SecurityLevel
from app.models.document import DocumentMetadata, DocumentChunk

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_test_documents():
    """
    Seeds test documents in ChromaStore across HR and Engineering departments.
    """
    hr_meta = DocumentMetadata(
        doc_id="doc_hr_salary_test",
        title="HR Salary and Compensation Policy",
        department="HR",
        security_level="Confidential",
        allowed_roles=["HR", "Executive"],
        owner="HR Team",
        file_type="docx"
    )

    eng_meta = DocumentMetadata(
        doc_id="doc_eng_standards_test",
        title="Software Engineering Coding Standards",
        department="Engineering",
        security_level="Internal",
        allowed_roles=["Engineering", "Executive"],
        owner="Engineering Lead",
        file_type="pdf"
    )

    hr_chunk = DocumentChunk(
        chunk_id="doc_hr_salary_test_chunk_0",
        doc_id="doc_hr_salary_test",
        text="Annual salary adjustments occur in Q1. Executive and HR approval required.",
        chunk_index=0,
        metadata=hr_meta
    )

    eng_chunk = DocumentChunk(
        chunk_id="doc_eng_standards_test_chunk_0",
        doc_id="doc_eng_standards_test",
        text="Python code must comply with PEP 8 and pass MyPy type checking.",
        chunk_index=0,
        metadata=eng_meta
    )

    chroma_store.add_documents([hr_chunk, eng_chunk])
    return {"hr_id": "doc_hr_salary_test", "eng_id": "doc_eng_standards_test"}


def test_metadata_filter_builder():
    filt = build_chroma_filter(department="HR", security_level="Internal")
    assert filt == {"$and": [{"department": "HR"}, {"security_level": "Internal"}]}

    single_filt = build_chroma_filter(department="Engineering")
    assert single_filt == {"department": "Engineering"}


def test_task_a1_metadata_filtering(setup_test_documents):
    # Department filter for HR
    hr_results = chroma_store.search("policy", k=5, filters={"department": "HR"})
    assert len(hr_results) >= 1
    for r in hr_results:
        assert r["metadata"]["department"] == "HR"

    # Department filter for Engineering
    eng_results = chroma_store.search("code", k=5, filters={"department": "Engineering"})
    assert len(eng_results) >= 1
    for r in eng_results:
        assert r["metadata"]["department"] == "Engineering"


def test_task_a1_rbac_cross_department_restriction(setup_test_documents):
    # Engineering user trying to retrieve HR Confidential documents
    eng_user = UserContext(
        user_id="eng_dev_01",
        username="Alice",
        role=UserRole.ENGINEERING,
        department=Department.ENGINEERING
    )

    results = chroma_store.search("salary adjustments compensation", k=5, user_context=eng_user)
    # Engineering user must NOT be granted access to HR Confidential salary chunks
    assert not any(r["metadata"].get("department") == "HR" and r["metadata"].get("security_level") == "Confidential" for r in results)

    # HR User trying the same query
    hr_user = UserContext(
        user_id="hr_manager_01",
        username="Bob",
        role=UserRole.HR,
        department=Department.HR
    )

    hr_results = chroma_store.search("salary adjustments compensation", k=5, user_context=hr_user)
    assert len(hr_results) >= 1
    assert any(r["metadata"].get("department") == "HR" for r in hr_results)


def test_task_a2_candidate_retrieval_functions(setup_test_documents):
    # Test retrieve_chunks
    chunks = retrieve_chunks("PEP 8 code standards", k=4)
    assert len(chunks) >= 1
    assert any(c["metadata"].get("department") == "Engineering" for c in chunks)

    # Test retrieve_documents
    docs = retrieve_documents("PEP 8 code standards", k=4)
    assert len(docs) >= 1
    assert "doc_id" in docs[0]
    assert "matching_chunks" in docs[0]

    # Test retrieve_with_filters
    filt_chunks = retrieve_with_filters("salary", department="HR", k=4)
    assert len(filt_chunks) >= 1
    assert filt_chunks[0]["metadata"]["department"] == "HR"


def test_task_a2_retrieval_api_endpoint(setup_test_documents):
    # Test POST /api/v1/retrieval/search
    response = client.post(
        "/api/v1/retrieval/search",
        json={
            "query": "PEP 8 MyPy",
            "department": "Engineering",
            "k": 3
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "PEP 8 MyPy"
    assert data["candidate_count"] >= 1
    assert data["results"][0]["metadata"]["department"] == "Engineering"

    # Test POST /api/v1/retrieval/documents
    doc_response = client.post(
        "/api/v1/retrieval/documents",
        json={
            "query": "PEP 8",
            "k": 2
        }
    )
    assert doc_response.status_code == 200
    doc_data = doc_response.json()
    assert doc_data["candidate_count"] >= 1
    assert "matching_chunks" in doc_data["results"][0]
