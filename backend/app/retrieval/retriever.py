import logging
from typing import List, Dict, Any, Optional
from app.database.chroma_store import chroma_store, build_chroma_filter
from app.retrieval.hybrid_search import hybrid_retriever
from app.rbac.roles import UserContext

logger = logging.getLogger(__name__)


def retrieve_chunks(
    query: str,
    k: int = 4,
    filters: Optional[Dict[str, Any]] = None,
    user_context: Optional[UserContext] = None,
    hybrid: bool = True
) -> List[Dict[str, Any]]:
    """
    Task A2 / Task A3: Retrieves candidate text chunks matching a query.
    Supports hybrid (Vector + BM25) search by default or pure vector search when hybrid=False.
    """
    logger.info(f"Retrieving chunks (hybrid={hybrid}) for query='{query}', k={k}, filters={filters}")
    
    if hybrid:
        return hybrid_retriever.search(
            query=query,
            k=k,
            filters=filters,
            user_context=user_context
        )
    else:
        return chroma_store.search(
            query=query,
            k=k,
            filters=filters,
            user_context=user_context
        )


def retrieve_documents(
    query: str,
    k: int = 4,
    filters: Optional[Dict[str, Any]] = None,
    user_context: Optional[UserContext] = None,
    hybrid: bool = True
) -> List[Dict[str, Any]]:
    """
    Retrieves distinct candidate documents matching a query.
    Groups matching chunks by doc_id and aggregates metadata and scores.
    """
    chunks = retrieve_chunks(query=query, k=k * 2, filters=filters, user_context=user_context, hybrid=hybrid)

    doc_map: Dict[str, Dict[str, Any]] = {}
    for chunk in chunks:
        doc_id = chunk["metadata"].get("doc_id")
        if not doc_id:
            continue

        if doc_id not in doc_map:
            doc_map[doc_id] = {
                "doc_id": doc_id,
                "title": chunk["metadata"].get("title", ""),
                "department": chunk["metadata"].get("department", ""),
                "security_level": chunk["metadata"].get("security_level", ""),
                "owner": chunk["metadata"].get("owner", ""),
                "file_type": chunk["metadata"].get("file_type", ""),
                "max_score": chunk["score"],
                "matching_chunks": [
                    {
                        "chunk_id": chunk["chunk_id"],
                        "text": chunk["text"],
                        "score": chunk["score"]
                    }
                ]
            }
        else:
            doc_map[doc_id]["matching_chunks"].append({
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "score": chunk["score"]
            })
            if chunk["score"] > doc_map[doc_id]["max_score"]:
                doc_map[doc_id]["max_score"] = chunk["score"]

    distinct_docs = list(doc_map.values())
    distinct_docs.sort(key=lambda d: d["max_score"], reverse=True)
    return distinct_docs[:k]


def retrieve_with_filters(
    query: str,
    department: Optional[str] = None,
    security_level: Optional[str] = None,
    user_context: Optional[UserContext] = None,
    k: int = 4,
    hybrid: bool = True
) -> List[Dict[str, Any]]:
    """
    Convenience helper to retrieve candidate chunks using explicit department,
    security_level, and RBAC user context filters.
    """
    chroma_where = build_chroma_filter(
        department=department,
        security_level=security_level
    )
    return retrieve_chunks(
        query=query,
        k=k,
        filters=chroma_where,
        user_context=user_context,
        hybrid=hybrid
    )
