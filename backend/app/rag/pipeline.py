"""
High-level RAG Pipeline orchestration.
Connects vector retrieval to TicketState and provides execution helpers.
"""
import logging
from typing import Optional
from app.models.schemas import TicketState
from app.rag.prompts import format_retrieved_context_prompt
from app.rag.retriever import FAQRetriever, RetrievedDocument

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    End-to-end RAG orchestrator for ticket processing.
    """

    def __init__(self, retriever: Optional[FAQRetriever] = None):
        self.retriever = retriever or FAQRetriever()

    def process_ticket(
        self,
        state: TicketState,
        top_k: int = 3,
        use_topic_filter: bool = True,
    ) -> TicketState:
        """
        Execute RAG retrieval for a TicketState and update its RAG tracking fields.
        Guarantees that errors do not crash the workflow.
        """
        query = state.subject or ""
        state.rag_query = query

        if not query.strip():
            logger.warning("Empty ticket subject; skipping RAG retrieval.")
            state.rag_used = False
            state.retrieval_count = 0
            state.retrieved_context = "No ticket text provided for knowledge retrieval."
            state.retrieved_sources = []
            state.used_sources = []
            state.retrieval_scores = []
            state.retrieval_metadata = []
            state.retrieval_latency_ms = 0.0
            state.total_retrieval_ms = 0.0
            state.embedding_query_ms = 0.0
            state.vector_search_ms = 0.0
            state.is_cold_retrieval = False
            return state

        filter_topic = state.topic if use_topic_filter else None

        try:
            retrieved_docs, latency_ms = self.retriever.retrieve(
                query=query,
                top_k=top_k,
                filter_topic=filter_topic,
            )

            state.retrieval_latency_ms = latency_ms
            state.total_retrieval_ms = latency_ms
            state.retrieval_count = len(retrieved_docs)

            timings = getattr(self.retriever, "last_timings", {})
            state.embedding_query_ms = timings.get("embedding_query_ms", 0.0)
            state.vector_search_ms = timings.get("vector_search_ms", 0.0)
            state.is_cold_retrieval = timings.get("is_cold", False)
            state.used_sources = []

            if retrieved_docs:
                state.rag_used = True
                state.retrieved_sources = [doc.to_citation() for doc in retrieved_docs]
                state.retrieval_scores = [round(doc.score, 4) for doc in retrieved_docs]
                state.retrieval_metadata = [doc.metadata for doc in retrieved_docs]
                state.retrieved_context = format_retrieved_context_prompt(
                    [doc.to_dict() for doc in retrieved_docs]
                )
                state.rag_error = None
            else:
                state.rag_used = False
                state.retrieved_sources = []
                state.used_sources = []
                state.retrieval_scores = []
                state.retrieval_metadata = []
                state.retrieved_context = "No matching verified FAQ articles found in the knowledge base."
                state.rag_error = None

        except Exception as e:
            logger.error(f"RAG retrieval encountered an error: {e}", exc_info=True)
            state.rag_used = False
            state.rag_error = str(e)
            state.retrieval_count = 0
            state.retrieved_sources = []
            state.used_sources = []
            state.retrieval_scores = []
            state.retrieval_metadata = []
            state.total_retrieval_ms = None
            state.embedding_query_ms = None
            state.vector_search_ms = None
            state.retrieved_context = (
                f"Knowledge retrieval temporarily unavailable due to system error: {e}"
            )

        return state
