import os
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.database.eval_db import eval_db
from app.database.chroma_store import chroma_store

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics & Observability API"])


@router.get("/evaluation")
async def get_evaluation_analytics():
    """
    Task A2: Returns RAG quality evaluation summary (Faithfulness, Precision, Recall, Hallucination Rate, Relevancy).
    """
    try:
        summary = eval_db.get_evaluation_summary()
        recent_evals = eval_db.get_recent_evaluations(limit=10)
        return {
            "summary": summary,
            "recent_evaluations": recent_evals
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch evaluation analytics: {str(e)}")


@router.get("/cost")
async def get_cost_analytics():
    """
    Task A4: Returns cost, token consumption, latency breakdown, and cache hit metrics.
    """
    try:
        telemetry = eval_db.get_telemetry_summary()
        return {
            "total_queries": telemetry["total_queries"],
            "avg_tokens_per_query": telemetry["avg_tokens"],
            "total_tokens_consumed": telemetry["sum_tokens"],
            "total_cost_usd": telemetry["total_cost"],
            "avg_cost_per_query_usd": telemetry["avg_cost"],
            "cache_hit_rate": telemetry["cache_hit_rate"],
            "latency_breakdown_ms": {
                "retrieval": telemetry["avg_retrieval_ms"],
                "embedding": telemetry["avg_embedding_ms"],
                "reranker": telemetry["avg_reranker_ms"],
                "llm": telemetry["avg_llm_ms"],
                "total": telemetry["avg_total_ms"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch cost analytics: {str(e)}")


@router.get("/documents")
async def get_document_analytics():
    """
    Task A5: Returns document counts, total chunks, storage usage, and department distribution.
    """
    try:
        all_records = chroma_store.collection.get(include=["metadatas", "documents"])
        metadatas = all_records.get("metadatas", []) or []
        documents = all_records.get("documents", []) or []

        total_chunks = len(metadatas)
        unique_docs = set()
        dept_counts: Dict[str, int] = {
            "HR": 0,
            "Engineering": 0,
            "Finance": 0,
            "Legal": 0,
            "Sales": 0
        }
        total_chars = 0

        for meta in metadatas:
            doc_id = meta.get("doc_id")
            if doc_id:
                unique_docs.add(doc_id)

            dept = meta.get("department", "General")
            if dept in dept_counts:
                dept_counts[dept] += 1
            else:
                dept_counts[dept] = dept_counts.get(dept, 0) + 1

        for doc_text in documents:
            total_chars += len(doc_text)

        avg_chunk_size = round(total_chars / total_chunks, 1) if total_chunks > 0 else 800.0
        # Estimate storage usage in MBs
        estimated_storage_mb = round((total_chars * 2 + total_chunks * 384 * 4) / (1024 * 1024), 2)

        return {
            "total_documents": len(unique_docs),
            "total_chunks": total_chunks,
            "total_embeddings": total_chunks,
            "avg_chunk_size": avg_chunk_size,
            "storage_usage_mb": max(0.05, estimated_storage_mb),
            "department_distribution": dept_counts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch document analytics: {str(e)}")
