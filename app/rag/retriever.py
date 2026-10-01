"""
Retriever component for semantic search over canonical FAQ documents.

Supports:
- Vector similarity search (top_k)
- Coarse topic to fine-grained Kaggle category metadata filtering
- Fallback to global search if filtered search returns empty
- Documented mapping integration via prompts.TOPIC_TO_CATEGORIES_MAP
"""
from dataclasses import dataclass
import logging
import time
from typing import Any, Optional
from app.rag.prompts import TOPIC_TO_CATEGORIES_MAP
from app.rag.vector_store import ChromaVectorStore

logger = logging.getLogger(__name__)


@dataclass
class RetrievedDocument:
    """Standardized retrieved FAQ document representation."""
    faq_id: str
    category: str
    score: float
    text: str
    metadata: dict[str, Any]

    def to_citation(self) -> dict[str, Any]:
        """Convert into citation metadata dictionary."""
        return {
            "faq_id": self.faq_id,
            "category": self.category,
            "score": round(self.score, 4),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "faq_id": self.faq_id,
            "category": self.category,
            "score": self.score,
            "text": self.text,
            "metadata": self.metadata,
        }


class FAQRetriever:
    """
    Retrieves canonical FAQ documents matching user inquiries.
    """

    def __init__(
        self,
        vector_store: Optional[ChromaVectorStore] = None,
        default_top_k: int = 3,
        min_relevance_score: float = 0.0,
    ):
        self.vector_store = vector_store or ChromaVectorStore()
        self.default_top_k = default_top_k
        self.min_relevance_score = min_relevance_score
        self.last_timings: dict[str, Any] = {
            "embedding_query_ms": 0.0,
            "vector_search_ms": 0.0,
            "total_retrieval_ms": 0.0,
            "is_cold": False,
        }

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_topic: Optional[str] = None,
        strict_category_filter: bool = False,
    ) -> tuple[list[RetrievedDocument], float]:
        """
        Retrieve relevant FAQ documents for a given query string with timing metrics.
        
        Args:
            query: The ticket issue description or search query.
            top_k: Number of documents to retrieve (default: 3).
            filter_topic: Optional coarse topic ('billing', 'shipping', 'technical', 'other')
                          used to filter by Kaggle categories.
            strict_category_filter: If True, do not fall back to global search if filtered
                                    results are empty.
                                    
        Returns:
            Tuple of (list[RetrievedDocument], latency_ms)
        """
        start_time = time.perf_counter()
        k = top_k if top_k is not None else self.default_top_k

        if not query or not query.strip():
            logger.warning("Empty query provided to FAQRetriever.")
            empty_latency = round((time.perf_counter() - start_time) * 1000, 2)
            self.last_timings = {
                "embedding_query_ms": 0.0,
                "vector_search_ms": 0.0,
                "total_retrieval_ms": empty_latency,
                "is_cold": False,
            }
            return [], empty_latency

        # Check if underlying embedding model is cold before query
        is_cold = not getattr(self.vector_store.embedding_model, "is_loaded", True)

        # Build where filter if topic mapping applies
        where_filter = None
        if filter_topic:
            normalized_topic = filter_topic.lower().strip()
            categories = TOPIC_TO_CATEGORIES_MAP.get(normalized_topic)
            if categories:
                if len(categories) == 1:
                    where_filter = {"category": categories[0]}
                else:
                    where_filter = {"category": {"$in": categories}}

        results: list[dict[str, Any]] = []
        embedding_query_ms = 0.0
        vector_search_ms = 0.0

        # 1. Attempt filtered retrieval if filter is specified
        if where_filter:
            try:
                results = self.vector_store.query(
                    query_text=query,
                    top_k=k,
                    where=where_filter,
                )
                timings = getattr(self.vector_store, "last_query_timings", {})
                embedding_query_ms += timings.get("embedding_query_ms", 0.0)
                vector_search_ms += timings.get("vector_search_ms", 0.0)
            except Exception as e:
                logger.warning(f"Filtered query failed with filter {where_filter}: {e}")
                results = []

        # 2. If filtered results are empty or top score is weak (< 0.40), inspect global search
        top_score = results[0]["score"] if results else 0.0
        if (not results or top_score < 0.40) and not strict_category_filter:
            try:
                global_results = self.vector_store.query(
                    query_text=query,
                    top_k=k,
                    where=None,
                )
                timings = getattr(self.vector_store, "last_query_timings", {})
                # If filtered was not run or empty, use global timings; else accumulate
                if not results:
                    embedding_query_ms = timings.get("embedding_query_ms", 0.0)
                    vector_search_ms = timings.get("vector_search_ms", 0.0)
                else:
                    embedding_query_ms += timings.get("embedding_query_ms", 0.0)
                    vector_search_ms += timings.get("vector_search_ms", 0.0)

                if global_results:
                    global_top_score = global_results[0]["score"]
                    if not results or global_top_score > top_score:
                        results = global_results
            except Exception as e:
                if not results:
                    raise
                logger.warning(f"Global fallback query failed: {e}")

        total_retrieval_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # Filter by minimum relevance threshold and convert to RetrievedDocument
        retrieved_docs: list[RetrievedDocument] = []
        for r in results:
            score = float(r.get("score", 0.0))
            if score >= self.min_relevance_score:
                meta = r.get("metadata", {})
                retrieved_docs.append(
                    RetrievedDocument(
                        faq_id=str(r.get("faq_id", meta.get("faq_id", "UNKNOWN"))),
                        category=str(meta.get("category", "General")),
                        score=score,
                        text=str(r.get("text", "")),
                        metadata=meta,
                    )
                )

        # Check if cold start occurred during this retrieval
        if getattr(self.vector_store.embedding_model, "_just_loaded", False):
            is_cold = True

        self.last_timings = {
            "embedding_query_ms": round(embedding_query_ms, 2),
            "vector_search_ms": round(vector_search_ms, 2),
            "total_retrieval_ms": total_retrieval_ms,
            "is_cold": is_cold,
        }

        logger.info(
            f"Retrieved {len(retrieved_docs)} docs for query '{query[:40]}...' "
            f"(topic_filter={filter_topic}) in {total_retrieval_ms:.2f}ms "
            f"[embed={embedding_query_ms:.2f}ms, search={vector_search_ms:.2f}ms, cold={is_cold}]"
        )
        return retrieved_docs, total_retrieval_ms

    def retrieve_with_metrics(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_topic: Optional[str] = None,
        strict_category_filter: bool = False,
    ) -> tuple[list[RetrievedDocument], dict[str, Any]]:
        """Retrieve documents alongside granular timing metrics dictionary."""
        docs, _ = self.retrieve(
            query=query,
            top_k=top_k,
            filter_topic=filter_topic,
            strict_category_filter=strict_category_filter,
        )
        return docs, self.last_timings
