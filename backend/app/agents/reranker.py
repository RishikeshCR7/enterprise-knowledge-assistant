import math
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Cross-Encoder model name for pass/query re-ranking
CROSS_ENCODER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def compute_confidence_score(reranked_chunks: List[Dict[str, Any]]) -> int:
    """
    Computes an aggregate Confidence Score (0-100%) based on top reranker relevance scores.
    Handles Cross-Encoder logits, RRF scores, and raw vector similarity distances.
    """
    if not reranked_chunks:
        return 0

    top_chunk = reranked_chunks[0]

    # 1. If Cross-Encoder logit is present (typically -10 to +10)
    if "rerank_score" in top_chunk:
        top_score = top_chunk["rerank_score"]
        prob = 1.0 / (1.0 + math.exp(-float(top_score)))
        confidence = int(round(prob * 100))
        return max(15, min(99, confidence))

    # 2. If RRF score or similarity score is present
    top_score = top_chunk.get("rrf_score", top_chunk.get("score", 0.0))
    if isinstance(top_score, (float, int)):
        if top_score <= 0.04:
            # Max RRF score for rank #1 in vector and rank #1 in BM25 is ~0.03278
            prob = min(1.0, float(top_score) / 0.03278)
            confidence = int(round(prob * 95))
            return max(15, min(99, confidence))
        elif top_score <= 1.0:
            confidence = int(round(float(top_score) * 100))
            return max(15, min(99, confidence))
        else:
            prob = 1.0 / (1.0 + math.exp(-float(top_score)))
            confidence = int(round(prob * 100))
            return max(15, min(99, confidence))

    return 50


def deduplicate_sources(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates retrieved chunks into unique cited sources strictly by document Title.
    """
    seen_titles: Dict[str, Dict[str, Any]] = {}
    
    for idx, chunk in enumerate(chunks, 1):
        meta = chunk.get("metadata", {})
        if hasattr(meta, "to_chroma_metadata"):
            meta = meta.to_chroma_metadata()

        title = meta.get("title") or meta.get("doc_id") or f"Document {idx}"
        title_key = title.strip().lower()
        dept = meta.get("department", "General")
        sec_level = meta.get("security_level", "Internal")
        doc_id = meta.get("doc_id", f"doc_{idx}")
        score = chunk.get("rerank_score", chunk.get("score", 0.0))

        if title_key not in seen_titles:
            seen_titles[title_key] = {
                "source_id": len(seen_titles) + 1,
                "title": title,
                "department": dept,
                "security_level": sec_level,
                "doc_id": doc_id,
                "score": score,
                "text": chunk.get("text", ""),
                "chunk_count": 1
            }
        else:
            seen_titles[title_key]["chunk_count"] += 1
            if score > seen_titles[title_key]["score"]:
                seen_titles[title_key]["score"] = score

    return list(seen_titles.values())


class CrossEncoderReranker:
    def __init__(self, model_name: str = CROSS_ENCODER_MODEL_NAME):
        self.model_name = model_name
        self._model = None
        self._model_failed = False

    @property
    def model(self):
        if self._model is None and not self._model_failed:
            try:
                from sentence_transformers import CrossEncoder
                logger.info(f"Loading CrossEncoder model '{self.model_name}'...")
                self._model = CrossEncoder(self.model_name)
                logger.info("CrossEncoder model loaded successfully.")
            except Exception as e:
                logger.warning(f"Could not load CrossEncoder model '{self.model_name}': {str(e)}. Falling back to vector score sorting.")
                self._model_failed = True
        return self._model

    def rerank(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Task B3: Reranks candidate text chunks using a Cross-Encoder model.
        Computes joint (query, chunk_text) relevance scores.
        """
        if not chunks:
            return []

        if self.model is not None:
            try:
                pairs = [[query, chunk.get("text", "")] for chunk in chunks]
                scores = self.model.predict(pairs)
                
                # Attach cross-encoder scores to chunks
                reranked_chunks = []
                for idx, chunk in enumerate(chunks):
                    chunk_copy = dict(chunk)
                    chunk_copy["rerank_score"] = float(scores[idx])
                    reranked_chunks.append(chunk_copy)

                # Sort by rerank_score descending
                reranked_chunks.sort(key=lambda c: c["rerank_score"], reverse=True)
                logger.info(f"Cross-encoder reranked {len(chunks)} chunks down to top {top_k}.")
                return reranked_chunks[:top_k]
            except Exception as e:
                logger.error(f"Error during CrossEncoder prediction: {str(e)}")

        # Fallback: Sort by initial vector similarity score
        sorted_chunks = sorted(chunks, key=lambda c: c.get("score", 0.0), reverse=True)
        return sorted_chunks[:top_k]


# Global Reranker instance
reranker = CrossEncoderReranker()
