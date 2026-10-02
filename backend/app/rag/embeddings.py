"""
Embedding model abstraction and implementations for RAG.

Supports:
- Local SentenceTransformer (default: all-MiniLM-L6-v2)
- MockEmbeddings for fast, offline testing without downloading weights
"""
from abc import ABC, abstractmethod
import hashlib
import logging
from typing import Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


class BaseEmbeddingModel(ABC):
    """Abstract base class for all RAG embedding models."""

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Compute embeddings for a list of document strings."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Compute embedding for a single user query string."""
        pass


_GLOBAL_MODEL_CACHE: dict[str, Any] = {}
_GLOBAL_EMBEDDING_INSTANCES: dict[str, BaseEmbeddingModel] = {}
_MODEL_LOAD_TIMES_MS: dict[str, float] = {}


def is_model_loaded(model_name: Optional[str] = None) -> bool:
    """Check if the specified SentenceTransformer model is currently loaded in memory."""
    target = model_name or DEFAULT_EMBEDDING_MODEL
    return target in _GLOBAL_MODEL_CACHE


def get_model_load_time_ms(model_name: Optional[str] = None) -> Optional[float]:
    """Retrieve the one-time cold-start load time (in ms) for the specified model if recorded."""
    target = model_name or DEFAULT_EMBEDDING_MODEL
    return _MODEL_LOAD_TIMES_MS.get(target)


def reset_embedding_cache():
    """Reset cached embedding models and instances (primarily used for unit testing)."""
    global _GLOBAL_MODEL_CACHE, _GLOBAL_EMBEDDING_INSTANCES, _MODEL_LOAD_TIMES_MS
    _GLOBAL_MODEL_CACHE.clear()
    _GLOBAL_EMBEDDING_INSTANCES.clear()
    _MODEL_LOAD_TIMES_MS.clear()


class SentenceTransformerEmbeddings(BaseEmbeddingModel):
    """
    Local embedding model powered by sentence-transformers.
    Free, local, runs on CPU or GPU without external API dependencies.
    Reuses globally cached model weights across all requests.
    """

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL):
        self.model_name = model_name
        self._just_loaded = False

    @property
    def is_loaded(self) -> bool:
        """Whether the underlying SentenceTransformer model is in memory."""
        return self.model_name in _GLOBAL_MODEL_CACHE

    def warmup(self, sample_text: str = "warmup query") -> float:
        """
        Pre-load weights into memory and run a warm-up inference.
        Returns total warmup latency in milliseconds.
        """
        import time
        t0 = time.perf_counter()
        _ = self.embed_query(sample_text)
        return round((time.perf_counter() - t0) * 1000, 2)

    def _get_model(self):
        self._just_loaded = False
        if self.model_name not in _GLOBAL_MODEL_CACHE:
            import time
            t0 = time.perf_counter()
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading SentenceTransformer model '{self.model_name}' (cold-start initialization)...")
                _GLOBAL_MODEL_CACHE[self.model_name] = SentenceTransformer(self.model_name)
                load_time_ms = round((time.perf_counter() - t0) * 1000, 2)
                _MODEL_LOAD_TIMES_MS[self.model_name] = load_time_ms
                self._just_loaded = True
                logger.info(f"SentenceTransformer '{self.model_name}' loaded in {load_time_ms:.2f}ms.")
            except Exception as e:
                logger.error(f"Failed to load SentenceTransformer '{self.model_name}': {e}")
                raise RuntimeError(
                    f"Could not load SentenceTransformer model '{self.model_name}'. "
                    f"Ensure 'sentence-transformers' is installed. Error: {e}"
                ) from e
        return _GLOBAL_MODEL_CACHE[self.model_name]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> list[float]:
        if not text or not str(text).strip():
            text = " "
        model = self._get_model()
        embedding = model.encode([text], convert_to_numpy=True, show_progress_bar=False, normalize_embeddings=True)[0]
        return embedding.tolist()


class MockEmbeddings(BaseEmbeddingModel):
    """
    Deterministic pseudo-embedding model for offline testing and fast CI/CD execution.
    Generates consistent normalized vectors of dimension 384 based on string hashes.
    """

    def __init__(self, dim: int = EMBEDDING_DIM):
        self.dim = dim
        self._just_loaded = False

    @property
    def is_loaded(self) -> bool:
        return True

    def warmup(self, sample_text: str = "warmup query") -> float:
        return 0.0

    def _hash_to_vector(self, text: str) -> list[float]:
        # Generate reproducible pseudo-random vector based on text MD5
        h = hashlib.md5(text.encode("utf-8")).hexdigest()
        seed = int(h[:8], 16)
        rng = np.random.RandomState(seed)
        vec = rng.randn(self.dim).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._hash_to_vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._hash_to_vector(text)


def get_embedding_model(
    model_name: Optional[str] = None,
    use_mock: bool = False,
) -> BaseEmbeddingModel:
    """
    Factory function to retrieve the configured embedding model.
    Reuses existing cached instances to prevent reloading.
    """
    if use_mock:
        return MockEmbeddings()
    target_model = model_name or DEFAULT_EMBEDDING_MODEL
    if target_model not in _GLOBAL_EMBEDDING_INSTANCES:
        _GLOBAL_EMBEDDING_INSTANCES[target_model] = SentenceTransformerEmbeddings(model_name=target_model)
    return _GLOBAL_EMBEDDING_INSTANCES[target_model]
