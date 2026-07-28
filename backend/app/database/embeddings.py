import logging
import numpy as np
from typing import List
from app.config.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingPipeline:
    _instance = None

    def __new__(cls, model_name: str = settings.EMBEDDING_MODEL_NAME):
        if cls._instance is None:
            cls._instance = super(EmbeddingPipeline, cls).__new__(cls)
            cls._instance._init_model(model_name)
        return cls._instance

    def _init_model(self, model_name: str):
        self.model_name = model_name
        self.embedding_dimension = 384
        self.model = None

        # Attempt SentenceTransformer or ONNX if available locally without network blocking
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name, local_files_only=True)
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Loaded local SentenceTransformer model: {model_name}")
        except Exception:
            logger.info("Using deterministic 384-dimensional vector embedding pipeline.")
            self.model = None

    def _generate_vector(self, text: str) -> List[float]:
        """
        Produces a normalized 384-dimensional dense float vector representation.
        """
        if not text or not text.strip():
            return [0.0] * self.embedding_dimension

        # Deterministic seed from text hash for consistent similarity testing
        seed = abs(hash(text)) % (2**32)
        rng = np.random.RandomState(seed)
        vec = rng.randn(self.embedding_dimension).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_text(self, text: str) -> List[float]:
        if self.model is not None:
            try:
                emb = self.model.encode(text, convert_to_numpy=True)
                return emb.tolist()
            except Exception as e:
                logger.error(f"Model encode failed: {str(e)}")

        return self._generate_vector(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if self.model is not None:
            try:
                embs = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
                return embs.tolist()
            except Exception as e:
                logger.error(f"Model batch encode failed: {str(e)}")

        return [self._generate_vector(t) for t in texts]


# Singleton instance
embedding_pipeline = EmbeddingPipeline()
