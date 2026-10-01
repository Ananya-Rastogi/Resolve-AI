"""
RAG (Retrieval-Augmented Generation) package for customer support ticket triage.

Components:
- loader: Document loading from deduplicated canonical FAQ dataset
- chunker: 1 FAQ = 1 Document chunking inspection and sizing
- embeddings: SentenceTransformers (all-MiniLM-L6-v2) & mock embeddings
- vector_store: ChromaDB local vector store persistence and CLI builder
- retriever: Semantic similarity retrieval with topic/category filtering
- prompts: System & user prompts, topic-to-category mapping, context formatting
- pipeline: High-level ticket RAG orchestration
"""
from app.rag.chunker import chunk_documents, inspect_document_lengths
from app.rag.embeddings import (
    BaseEmbeddingModel,
    MockEmbeddings,
    SentenceTransformerEmbeddings,
    get_embedding_model,
)
from app.rag.loader import Document, format_faq_document_text, load_canonical_faqs
from app.rag.pipeline import RAGPipeline
from app.rag.prompts import (
    CATEGORY_TO_TOPIC_MAP,
    RAG_RESPONSE_SYSTEM_PROMPT,
    RAG_RESPONSE_USER_PROMPT,
    TOPIC_TO_CATEGORIES_MAP,
    format_retrieved_context_prompt,
)
from app.rag.retriever import FAQRetriever, RetrievedDocument
from app.rag.vector_store import ChromaVectorStore

__all__ = [
    "Document",
    "load_canonical_faqs",
    "format_faq_document_text",
    "chunk_documents",
    "inspect_document_lengths",
    "BaseEmbeddingModel",
    "SentenceTransformerEmbeddings",
    "MockEmbeddings",
    "get_embedding_model",
    "ChromaVectorStore",
    "FAQRetriever",
    "RetrievedDocument",
    "RAGPipeline",
    "TOPIC_TO_CATEGORIES_MAP",
    "CATEGORY_TO_TOPIC_MAP",
    "RAG_RESPONSE_SYSTEM_PROMPT",
    "RAG_RESPONSE_USER_PROMPT",
    "format_retrieved_context_prompt",
]
