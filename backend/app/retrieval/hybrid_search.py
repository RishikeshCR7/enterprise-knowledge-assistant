import logging
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    BM25Okapi = None
    HAS_BM25 = False
    logger.warning("rank_bm25 package not installed. Hybrid search will fallback to vector search.")

from app.database.chroma_store import chroma_store, build_chroma_filter
from app.rbac.permissions import can_access_document
from app.rbac.roles import UserContext


def tokenize_text(text: str) -> List[str]:
    """
    Simple alphanumeric tokenizer for BM25 keyword matching.
    """
    if not text:
        return []
    return [token.lower() for token in re.findall(r'\b\w+\b', text)]


class BM25Indexer:
    """
    In-memory BM25 indexer wrapping rank_bm25.BM25Okapi over indexed ChromaDB document chunks.
    """
    def __init__(self):
        self.bm25: Optional[Any] = None
        self.corpus_chunks: List[Dict[str, Any]] = []
        self._is_indexed = False

    def build_index(self, force_refresh: bool = False):
        """
        Loads document chunks from ChromaDB and builds BM25 index.
        """
        if not HAS_BM25:
            return

        current_count = chroma_store.collection.count()
        if self._is_indexed and not force_refresh and len(self.corpus_chunks) == current_count:
            return

        all_records = chroma_store.collection.get(include=["documents", "metadatas"])
        if not all_records or not all_records.get("ids"):
            logger.warning("No documents found in ChromaDB to build BM25 index.")
            self.corpus_chunks = []
            self.bm25 = None
            self._is_indexed = True
            return

        ids = all_records["ids"]
        docs = all_records["documents"]
        metas = all_records["metadatas"]

        self.corpus_chunks = []
        tokenized_corpus = []

        for i in range(len(ids)):
            chunk_data = {
                "chunk_id": ids[i],
                "text": docs[i],
                "metadata": metas[i]
            }
            self.corpus_chunks.append(chunk_data)
            meta = metas[i]
            title = meta.get("title", "")
            tags = meta.get("tags", "")
            chunk_full_text = f"{title} {tags} {docs[i]}"
            tokens = tokenize_text(chunk_full_text)
            tokenized_corpus.append(tokens if tokens else [""])

        if tokenized_corpus and BM25Okapi is not None:
            self.bm25 = BM25Okapi(tokenized_corpus)
            logger.info(f"Successfully built BM25 index with {len(self.corpus_chunks)} document chunks.")
        
        self._is_indexed = True

    def search(
        self,
        query: str,
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        user_context: Optional[UserContext] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs BM25 keyword search over indexed chunks.
        """
        if not HAS_BM25:
            return []

        self.build_index()

        if not self.bm25 or not self.corpus_chunks:
            return []

        query_tokens = tokenize_text(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        
        # Rank by score descending
        scored_indices = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scored_indices:
            if score <= 0.0:
                continue

            chunk = self.corpus_chunks[idx]
            meta = chunk["metadata"]

            # Filter department if passed in filters
            if filters and "department" in filters:
                req_dept = filters["department"]
                if meta.get("department") != req_dept:
                    continue

            # RBAC authorization check
            if user_context and not can_access_document(user_context, meta):
                continue

            results.append({
                "chunk_id": chunk["chunk_id"],
                "text": chunk["text"],
                "metadata": meta,
                "score": float(score)
            })

            if len(results) >= k:
                break

        return results


class HybridRetriever:
    """
    Task A3: Combines Vector Search (ChromaDB) and BM25 Search using Reciprocal Rank Fusion (RRF).
    """
    def __init__(self):
        self.bm25_indexer = BM25Indexer()

    def reciprocal_rank_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        rrf_k: int = 60,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Calculates RRF score: RRF_score(d) = 1/(k + rank_vector(d)) + 1/(k + rank_bm25(d))
        """
        if not bm25_results:
            return vector_results[:top_k]

        scores: Dict[str, float] = {}
        chunk_map: Dict[str, Dict[str, Any]] = {}

        # Process vector ranks
        for rank, item in enumerate(vector_results, start=1):
            cid = item["chunk_id"]
            chunk_map[cid] = item
            scores[cid] = scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))

        # Process BM25 ranks
        for rank, item in enumerate(bm25_results, start=1):
            cid = item["chunk_id"]
            if cid not in chunk_map:
                chunk_map[cid] = item
            scores[cid] = scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))

        # Sort combined results by RRF score
        sorted_cids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)

        fused_results = []
        for cid in sorted_cids[:top_k]:
            chunk_copy = dict(chunk_map[cid])
            chunk_copy["rrf_score"] = round(scores[cid], 5)
            chunk_copy["score"] = round(scores[cid], 5)
            fused_results.append(chunk_copy)

        return fused_results

    def search(
        self,
        query: str,
        k: int = 4,
        filters: Optional[Dict[str, Any]] = None,
        user_context: Optional[UserContext] = None,
        vector_weight: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Task A3: Executes Hybrid Search combining Vector Search and BM25 Search.
        """
        fetch_k = k * 3

        # 1. Vector Search
        vector_results = chroma_store.search(
            query=query,
            k=fetch_k,
            filters=filters,
            user_context=user_context
        )

        # 2. BM25 Keyword Search
        bm25_results = self.bm25_indexer.search(
            query=query,
            k=fetch_k,
            filters=filters,
            user_context=user_context
        )

        # 3. Merge & Fuse via Reciprocal Rank Fusion
        fused = self.reciprocal_rank_fusion(
            vector_results=vector_results,
            bm25_results=bm25_results,
            rrf_k=60,
            top_k=k
        )

        logger.info(f"Hybrid search for '{query}' returned {len(fused)} fused chunks.")
        return fused


# Global HybridRetriever instance
hybrid_retriever = HybridRetriever()
