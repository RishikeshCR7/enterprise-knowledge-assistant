import logging
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config.settings import settings
from app.models.document import DocumentMetadata, DocumentChunk

logger = logging.getLogger(__name__)


class DocumentChunker:
    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, chunk_overlap: int = settings.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def chunk_document(self, doc_id: str, text: str, metadata: DocumentMetadata) -> List[DocumentChunk]:
        """
        Splits text into chunks of chunk_size 800 and chunk_overlap 150.
        Attaches chunk metadata and generates chunk_ids ({doc_id}_chunk_0, {doc_id}_chunk_1, etc.).
        """
        if not text or not text.strip():
            return []

        raw_chunks = self.text_splitter.split_text(text)
        document_chunks = []

        for idx, chunk_text in enumerate(raw_chunks):
            chunk_id = f"{doc_id}_chunk_{idx}"
            chunk_obj = DocumentChunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                text=chunk_text,
                chunk_index=idx,
                metadata=metadata
            )
            document_chunks.append(chunk_obj)

        logger.info(f"Chunked document '{doc_id}' into {len(document_chunks)} chunks (size={self.chunk_size}, overlap={self.chunk_overlap}).")
        return document_chunks


# Global DocumentChunker instance
chunker = DocumentChunker()
