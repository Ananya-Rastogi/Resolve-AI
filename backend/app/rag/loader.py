"""
Document loader for canonical FAQ records.
Loads preprocessed deduplicated FAQ data from CSV into structured Document objects.
"""
from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_FAQ_CSV_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "rag_faqs.csv"


@dataclass
class Document:
    """
    Searchable text document with associated structured metadata.
    """
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    doc_id: Optional[str] = None

    @property
    def page_content(self) -> str:
        """Alias for compatibility with standard retriever interfaces."""
        return self.text

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "text": self.text,
            "metadata": self.metadata,
        }


def format_faq_document_text(row: pd.Series | dict[str, Any]) -> str:
    """
    Format a canonical FAQ record into searchable document text per Phase 2 specifications.
    
    Format:
    Question: {question}
    Alternative Query: {alternative_question} (if present and distinct)
    Answer: {answer}
    Keywords: {keywords}
    """
    question = str(row.get("question", "")).strip()
    alt_question = str(row.get("alternative_question", "")).strip()
    answer = str(row.get("answer", "")).strip()
    keywords = str(row.get("keywords", "")).strip()

    parts = [f"Question: {question}"]
    if alt_question and alt_question != question and alt_question.lower() != "nan":
        parts.append(f"Alternative Query: {alt_question}")
    parts.append(f"Answer: {answer}")
    if keywords and keywords.lower() != "nan":
        parts.append(f"Keywords: {keywords}")

    return "\n".join(parts)


def load_canonical_faqs(csv_path: Optional[str | Path] = None) -> list[Document]:
    """
    Load canonical FAQ records from data/rag_faqs.csv and return structured Document objects.
    
    Raises:
        FileNotFoundError: If the canonical FAQ CSV file does not exist.
        ValueError: If the CSV is empty or missing essential columns.
    """
    path = Path(csv_path) if csv_path else DEFAULT_FAQ_CSV_PATH

    if not path.exists():
        raise FileNotFoundError(f"Canonical FAQ file not found at: {path}")

    df = pd.read_csv(path)
    if df.empty:
        raise ValueError(f"Canonical FAQ file is empty: {path}")

    required_cols = {"faq_id", "question", "answer", "category"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Canonical FAQ CSV missing required columns: {missing}")

    documents: list[Document] = []
    for _, row in df.iterrows():
        text = format_faq_document_text(row)
        faq_id = str(row["faq_id"])
        
        metadata = {
            "faq_id": faq_id,
            "question": str(row.get("question", "")),
            "answer": str(row.get("answer", "")),
            "category": str(row.get("category", "")),
            "subcategory": str(row.get("subcategory", "")),
            "intent": str(row.get("intent", "")),
            "response_type": str(row.get("response_type", "")),
            "difficulty_level": str(row.get("difficulty_level", "")),
            "language": str(row.get("language", "English")),
            "canonical_answer_id": int(row["canonical_answer_id"]) if pd.notna(row.get("canonical_answer_id")) else 0,
            "source_faq_id": str(row.get("source_faq_id", "")),
            "source_occurrences": int(row["source_occurrences"]) if pd.notna(row.get("source_occurrences")) else 1,
        }

        documents.append(
            Document(
                text=text,
                metadata=metadata,
                doc_id=faq_id,
            )
        )

    logger.info(f"Loaded {len(documents)} canonical FAQ documents from {path.name}")
    return documents
