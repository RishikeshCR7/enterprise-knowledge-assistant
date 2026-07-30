import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Cross-Encoder model name for pass/query re-ranking
CROSS_ENCODER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


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
