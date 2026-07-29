import os
import logging
from typing import List, Dict, Any, Optional
import chromadb

from app.config.settings import settings
from app.models.document import DocumentChunk, DocumentMetadata
from app.database.embeddings import embedding_pipeline
from app.rbac.permissions import can_access_document
from app.rbac.roles import UserContext

logger = logging.getLogger(__name__)


def build_chroma_filter(
    department: Optional[str] = None,
    security_level: Optional[str] = None,
    allowed_roles: Optional[List[str]] = None,
    custom_filters: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Builds a ChromaDB-compliant 'where' filter dictionary.
    Supports department, security_level, allowed_roles, and custom filters.
    """
    conditions = []

    if department:
        conditions.append({"department": department})

    if security_level:
        conditions.append({"security_level": security_level})

    if allowed_roles:
        if len(allowed_roles) == 1:
            conditions.append({"allowed_roles_str": {"$contains": allowed_roles[0]}})
        else:
            # Match any of the permitted roles
            role_conds = [{"allowed_roles_str": {"$contains": role}} for role in allowed_roles]
            conditions.append({"$or": role_conds})

    if custom_filters:
        for key, val in custom_filters.items():
            if isinstance(val, dict):
                conditions.append({key: val})
            else:
                conditions.append({key: val})

    if not conditions:
        return None
    elif len(conditions) == 1:
        return conditions[0]
    else:
        return {"$and": conditions}


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

    def search(
        self,
        query: str,
        k: int = 4,
        filters: Optional[Dict[str, Any]] = None,
        user_context: Optional[UserContext] = None
    ) -> List[Dict[str, Any]]:
        """
        Task A1: Performs vector search with metadata filtering and RBAC enforcement.
        """
        query_embedding = embedding_pipeline.embed_text(query)
        
        # Over-fetch if user_context is provided to guarantee top-k after RBAC filtering
        fetch_k = k * 3 if user_context else k

        kwargs: Dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": fetch_k,
        }
        if filters:
            kwargs["where"] = filters

        results = self.collection.query(**kwargs)
        
        formatted_results = []
        if results and results.get("ids") and results["ids"][0]:
            ids = results["ids"][0]
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(ids)

            for i in range(len(ids)):
                meta = metas[i]
                
                # Post-retrieval RBAC authorization check if user context is provided
                if user_context and not can_access_document(user_context, meta):
                    logger.debug(f"User {user_context.username} (Role: {user_context.role}) denied access to chunk {ids[i]}")
                    continue

                formatted_results.append({
                    "chunk_id": ids[i],
                    "text": docs[i],
                    "metadata": meta,
                    "score": round(1.0 - distances[i], 4) if distances[i] is not None else 1.0
                })

                if len(formatted_results) >= k:
                    break

        return formatted_results

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: Optional[Dict[str, Any]] = None,
        user_context: Optional[UserContext] = None
    ) -> List[Dict[str, Any]]:
        """
        Alias for search method to ensure backward compatibility.
        """
        return self.search(query=query, k=k, filters=filter, user_context=user_context)

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
