import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config.settings import settings
from app.models.document import DocumentChunk, DocumentMetadata
from app.database.embeddings import embedding_pipeline

logger = logging.getLogger(__name__)


class ChromaStore:
    def __init__(self, persist_dir: str = settings.CHROMA_PERSIST_DIR, collection_name: str = settings.COLLECTION_NAME):
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        os.makedirs(persist_dir, exist_ok=True)
        
        logger.info(f"Initializing ChromaDB client at '{persist_dir}'")
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"ChromaDB Collection '{collection_name}' initialized.")

    def add_documents(self, chunks: List[DocumentChunk]) -> int:
        """
        Adds document chunks and their vector embeddings to ChromaDB.
        """
        if not chunks:
            return 0

        ids = [chunk.chunk_id for chunk in chunks]
        texts = [chunk.text for chunk in chunks]
        metadatas = []
        
        for chunk in chunks:
            meta = chunk.metadata.to_chroma_metadata()
            meta["chunk_index"] = chunk.chunk_index
            metadatas.append(meta)

        # Check embeddings
        embeddings = []
        for chunk in chunks:
            if chunk.embedding:
                embeddings.append(chunk.embedding)
        
        if len(embeddings) != len(chunks):
            logger.info("Generating embeddings for chunks...")
            embeddings = embedding_pipeline.embed_documents(texts)

        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings
        )
        logger.info(f"Successfully added {len(chunks)} chunks to ChromaDB collection '{self.collection_name}'.")
        return len(chunks)

    def delete_document(self, doc_id: str) -> bool:
        """
        Deletes all chunks associated with a specific doc_id.
        """
        try:
            self.collection.delete(where={"doc_id": doc_id})
            logger.info(f"Deleted document chunks with doc_id: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {str(e)}")
            return False

    def similarity_search(self, query: str, k: int = 4, filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Performs vector similarity search against ChromaDB.
        """
        query_embedding = embedding_pipeline.embed_text(query)
        kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": k,
        }
        if filter:
            kwargs["where"] = filter

        results = self.collection.query(**kwargs)
        
        formatted_results = []
        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results else [0.0] * len(ids)

            for i in range(len(ids)):
                formatted_results.append({
                    "chunk_id": ids[i],
                    "text": docs[i],
                    "metadata": metas[i],
                    "score": 1.0 - distances[i] if distances[i] is not None else 1.0
                })

        return formatted_results

    def get_document(self, doc_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all chunks matching a doc_id.
        """
        results = self.collection.get(where={"doc_id": doc_id})
        formatted = []
        if results and results.get("ids"):
            ids = results["ids"]
            docs = results["documents"]
            metas = results["metadatas"]
            for i in range(len(ids)):
                formatted.append({
                    "chunk_id": ids[i],
                    "text": docs[i],
                    "metadata": metas[i]
                })
        return formatted

    def list_documents(self) -> List[DocumentMetadata]:
        """
        Returns unique documents indexed in ChromaDB.
        """
        all_records = self.collection.get(include=["metadatas"])
        if not all_records or not all_records.get("metadatas"):
            return []

        doc_dict: Dict[str, DocumentMetadata] = {}
        for meta in all_records["metadatas"]:
            doc_id = meta.get("doc_id")
            if doc_id and doc_id not in doc_dict:
                doc_dict[doc_id] = DocumentMetadata.from_chroma_metadata(meta)

        return list(doc_dict.values())


# Global ChromaStore instance
chroma_store = ChromaStore()
