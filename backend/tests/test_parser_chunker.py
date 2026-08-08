import os
import pytest
from app.ingestion.parser import DocumentParser
from app.ingestion.chunker import DocumentChunker
from app.models.document import DocumentMetadata

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))


def test_pdf_parser_and_chunker():
    pdf_path = os.path.join(DATA_DIR, "HR", "LeavePolicy.pdf")
    assert os.path.exists(pdf_path)

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    text, meta = DocumentParser.parse_pdf(file_bytes)
    assert "Leave Policy" in text or "Paid Time Off" in text or "Human Resources" in text
    assert meta["page_count"] >= 1

    chunker = DocumentChunker(chunk_size=800, chunk_overlap=150)
    doc_meta = DocumentMetadata(
        doc_id="test_hr_01",
        title="Leave Policy",
        department="HR",
        security_level="Confidential",
        allowed_roles=["HR", "Executive"],
        owner="HR Team",
        file_type="pdf"
    )
    chunks = chunker.chunk_document("test_hr_01", text, doc_meta)
    assert len(chunks) >= 1
    assert chunks[0].chunk_id == "test_hr_01_chunk_0"
    assert chunks[0].metadata.department == "HR"


def test_docx_parser():
    docx_path = os.path.join(DATA_DIR, "HR", "SalaryPolicy.docx")
    assert os.path.exists(docx_path)

    with open(docx_path, "rb") as f:
        file_bytes = f.read()

    text, meta = DocumentParser.parse_docx(file_bytes)
    assert "Compensation" in text
    assert meta["paragraph_count"] > 0
