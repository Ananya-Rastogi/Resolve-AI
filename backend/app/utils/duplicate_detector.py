"""
Duplicate ticket detection utility based on real database records.
Uses token overlap, Jaccard similarity, and sequence matching to identify similar tickets
without fabricating matches or performing destructive actions.
"""
import difflib
import re
from typing import Any, Dict, List, Optional

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
    "which", "this", "that", "these", "those", "then", "just", "so", "than",
    "such", "both", "through", "about", "for", "is", "of", "while", "during",
    "to", "from", "in", "out", "on", "off", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "any", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "can", "will",
    "don", "should", "now", "i", "me", "my", "myself", "we", "our", "you",
    "your", "he", "him", "she", "her", "it", "its", "they", "them", "please",
    "help", "issue", "problem", "having", "need", "with"
}


def _tokenize(text: str) -> set[str]:
    """Extract clean words from text excluding common stop words."""
    words = re.findall(r"\b[a-zA-Z0-9_\-#]+\b", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 1}


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate combined Jaccard and SequenceMatcher similarity score (0.0 to 1.0)."""
    if not text1 or not text2:
        return 0.0

    tokens1 = _tokenize(text1)
    tokens2 = _tokenize(text2)

    # Jaccard index
    union = tokens1 | tokens2
    if not union:
        jaccard = 0.0
    else:
        jaccard = len(tokens1 & tokens2) / len(union)

    # Sequence matcher for order and phrasing similarity
    seq_ratio = difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    # Weighted blend: Jaccard (60%) + Sequence (40%)
    score = (0.6 * jaccard) + (0.4 * seq_ratio)
    return round(score, 3)


def generate_similarity_reason(target: str, candidate: str, category: Optional[str], score: float) -> str:
    """Provide a brief, human-friendly explanation of why the issues are similar."""
    tokens1 = _tokenize(target)
    tokens2 = _tokenize(candidate)
    common = tokens1 & tokens2

    keywords_sample = ", ".join(f"'{w}'" for w in list(common)[:3]) if common else ""

    if score >= 0.70:
        base = "Nearly identical issue description"
    elif score >= 0.50:
        base = "Substantial overlap in customer concern"
    else:
        base = "Possible related topic"

    if keywords_sample:
        return f"{base} sharing key terms ({keywords_sample})."
    if category:
        return f"{base} in the {category} category."
    return f"{base}."


def find_duplicate_tickets(
    subject: str,
    existing_tickets: List[Dict[str, Any]],
    exclude_ticket_id: Optional[str] = None,
    threshold: float = 0.35,
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    Search actual existing tickets in the database for potential duplicates.
    Never auto-merges or deletes; returns candidates for human evaluation.
    """
    if not subject or not existing_tickets:
        return []

    matches = []
    for tkt in existing_tickets:
        cand_id = tkt.get("ticket_id")
        if not cand_id or (exclude_ticket_id and cand_id == exclude_ticket_id):
            continue

        cand_subj = tkt.get("subject") or ""
        score = calculate_similarity(subject, cand_subj)

        if score >= threshold:
            reason = generate_similarity_reason(
                subject, cand_subj, tkt.get("category"), score
            )
            matches.append({
                "ticket_id": cand_id,
                "subject": cand_subj,
                "similarity_score": score,
                "similarity_reason": reason,
                "status": tkt.get("status", "open"),
                "priority": tkt.get("priority", "Medium"),
                "category": tkt.get("category"),
                "created_at": tkt.get("created_at"),
            })

    # Sort by highest similarity first
    matches.sort(key=lambda m: m["similarity_score"], reverse=True)
    return matches[:max_results]
