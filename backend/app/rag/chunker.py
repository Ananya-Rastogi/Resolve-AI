"""
Chunking strategy for FAQ documents.

Phase 5 Strategy:
Since canonical FAQ documents are concise (typically 50-150 words / 200-800 characters)
and all-MiniLM-L6-v2 handles up to 256/512 tokens, we maintain:
ONE FAQ = ONE Searchable Knowledge Unit.
This keeps the question context, alternative phrasing, answer, and keywords intact.
"""
from dataclasses import dataclass
import logging
from typing import Optional
from app.rag.loader import Document

logger = logging.getLogger(__name__)

# all-MiniLM-L6-v2 context limit is 256 wordpiece tokens (approx 1000-1200 characters)
MAX_RECOMMENDED_CHARS = 1200


@dataclass
class ChunkingStats:
    """Summary statistics for chunked documents."""
    total_docs: int
    total_chunks: int
    min_chars: int
    max_chars: int
    avg_chars: float


def inspect_document_lengths(documents: list[Document]) -> ChunkingStats:
    """Compute character length statistics across loaded documents."""
    if not documents:
        return ChunkingStats(total_docs=0, total_chunks=0, min_chars=0, max_chars=0, avg_chars=0.0)

    lengths = [len(doc.text) for doc in documents]
    return ChunkingStats(
        total_docs=len(documents),
        total_chunks=len(documents),
        min_chars=min(lengths),
        max_chars=max(lengths),
        avg_chars=round(sum(lengths) / len(lengths), 2),
    )


def chunk_documents(
    documents: list[Document],
    max_chunk_chars: int = MAX_RECOMMENDED_CHARS,
) -> list[Document]:
    """
    Process FAQ documents into retrieval units.
    
    Adheres to Phase 5: Keeps 1 FAQ = 1 Document because all canonical FAQs
    fit comfortably within the embedding model's context window.
    """
    stats = inspect_document_lengths(documents)
    logger.info(
        f"Chunking inspection: {stats.total_docs} docs, "
        f"min length={stats.min_chars}, max length={stats.max_chars}, avg={stats.avg_chars} chars"
    )

    chunks: list[Document] = []
    for doc in documents:
        if len(doc.text) > max_chunk_chars:
            logger.warning(
                f"Document {doc.doc_id} has {len(doc.text)} chars (exceeds recommended {max_chunk_chars}). "
                "Retaining intact to preserve Question+Answer pairing."
            )
        chunks.append(doc)

    return chunks
