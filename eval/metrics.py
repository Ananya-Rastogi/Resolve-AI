"""
Core evaluation metrics module for Week 3 Quality Engineering.
Provides mathematically sound, independently verifiable calculation functions for:
- Multi-class classification (Accuracy, Macro/Per-class Precision, Recall, F1, Confusion Matrix)
- Information retrieval (Recall@K, Precision@K, MRR, nDCG@K)
- Grounding & Citations (ID validity, retrieval membership, abstention accuracy)
- System latency percentiles (P50, P95, P99, mean)
"""
from typing import Any, Dict, List, Optional, Sequence, Set, Union
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

# ---------------------------------------------------------------------------
# Classification Metrics
# ---------------------------------------------------------------------------

def compute_classification_metrics(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    labels: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """
    Compute comprehensive classification metrics including overall accuracy,
    macro precision/recall/F1, per-class breakdown, and confusion matrix.
    """
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")

    if not y_true:
        return {
            "accuracy": 0.0,
            "macro_precision": 0.0,
            "macro_recall": 0.0,
            "macro_f1": 0.0,
            "per_class": {},
            "confusion_matrix": [],
            "labels": [],
            "sample_count": 0,
        }

    # Determine ordered class labels
    if labels is None:
        unique_labels = sorted(list(set(y_true) | set(y_pred)))
    else:
        unique_labels = list(labels)

    acc = float(accuracy_score(y_true, y_pred))
    macro_prec = float(precision_score(y_true, y_pred, labels=unique_labels, average="macro", zero_division=0))
    macro_rec = float(recall_score(y_true, y_pred, labels=unique_labels, average="macro", zero_division=0))
    macro_f1 = float(f1_score(y_true, y_pred, labels=unique_labels, average="macro", zero_division=0))

    prec_per_class = precision_score(y_true, y_pred, labels=unique_labels, average=None, zero_division=0)
    rec_per_class = recall_score(y_true, y_pred, labels=unique_labels, average=None, zero_division=0)
    f1_per_class = f1_score(y_true, y_pred, labels=unique_labels, average=None, zero_division=0)

    per_class_dict = {}
    for idx, label in enumerate(unique_labels):
        support = sum(1 for y in y_true if y == label)
        per_class_dict[label] = {
            "precision": round(float(prec_per_class[idx]), 4),
            "recall": round(float(rec_per_class[idx]), 4),
            "f1": round(float(f1_per_class[idx]), 4),
            "support": int(support),
        }

    cm = confusion_matrix(y_true, y_pred, labels=unique_labels).tolist()

    return {
        "accuracy": round(acc, 4),
        "macro_precision": round(macro_prec, 4),
        "macro_recall": round(macro_rec, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": per_class_dict,
        "confusion_matrix": cm,
        "labels": unique_labels,
        "sample_count": len(y_true),
    }


# ---------------------------------------------------------------------------
# RAG Retrieval Metrics
# ---------------------------------------------------------------------------

def compute_recall_at_k(retrieved_ids: Sequence[str], expected_ids: Sequence[str], k: int) -> float:
    """
    Calculate Recall@K: 1.0 if at least one expected document is in top-K, else 0.0.
    For queries with no expected documents (unsupported), returns 1.0 if empty, else 0.0.
    """
    if not expected_ids:
        return 1.0 if not retrieved_ids[:k] else 0.0

    expected_set = {str(eid).strip().upper() for eid in expected_ids}
    top_k_set = {str(rid).strip().upper() for rid in retrieved_ids[:k]}

    return 1.0 if (expected_set & top_k_set) else 0.0


def compute_precision_at_k(retrieved_ids: Sequence[str], expected_ids: Sequence[str], k: int) -> float:
    """
    Calculate Precision@K: Fraction of top-K retrieved documents that are relevant.
    """
    if k <= 0:
        return 0.0

    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0

    expected_set = {str(eid).strip().upper() for eid in expected_ids}
    hits = sum(1 for rid in top_k if str(rid).strip().upper() in expected_set)
    return float(hits / min(k, len(top_k)))


def compute_reciprocal_rank(retrieved_ids: Sequence[str], expected_ids: Sequence[str]) -> float:
    """
    Calculate Reciprocal Rank (RR): 1 / rank of first relevant item in retrieved list.
    Returns 0.0 if no relevant items are retrieved.
    """
    if not expected_ids:
        return 0.0

    expected_set = {str(eid).strip().upper() for eid in expected_ids}
    for rank, rid in enumerate(retrieved_ids, 1):
        if str(rid).strip().upper() in expected_set:
            return 1.0 / rank

    return 0.0


def compute_ndcg_at_k(retrieved_ids: Sequence[str], expected_ids: Sequence[str], k: int) -> float:
    """
    Compute Normalized Discounted Cumulative Gain (nDCG@K) using standard binary relevance.
    """
    if not expected_ids or k <= 0:
        return 0.0

    expected_set = {str(eid).strip().upper() for eid in expected_ids}
    top_k = retrieved_ids[:k]

    # Calculate Discounted Cumulative Gain (DCG)
    dcg = 0.0
    for i, rid in enumerate(top_k):
        rel = 1.0 if str(rid).strip().upper() in expected_set else 0.0
        dcg += rel / np.log2(i + 2)  # i+2 because rank is 1-indexed (log2(1+1)=1)

    # Ideal Discounted Cumulative Gain (IDCG)
    ideal_hits = min(len(expected_set), k)
    if ideal_hits == 0:
        return 0.0

    idcg = sum(1.0 / np.log2(i + 2) for i in range(ideal_hits))

    return float(dcg / idcg) if idcg > 0.0 else 0.0


def aggregate_retrieval_metrics(
    eval_items: Sequence[Dict[str, Any]],
    k_values: Sequence[int] = (1, 3, 5),
) -> Dict[str, Any]:
    """
    Aggregate Recall@K, Precision@K, MRR, nDCG@K, empty retrieval rate,
    and retrieval latencies across a collection of evaluation queries.
    """
    if not eval_items:
        return {
            "total_queries": 0,
            "supported_queries": 0,
            "unsupported_queries": 0,
            "recall": {},
            "precision": {},
            "mrr": 0.0,
            "ndcg": {},
            "empty_retrieval_rate": 0.0,
        }

    # Filter to supported queries that actually have expected FAQ IDs for ranking metrics
    supported_items = [it for it in eval_items if it.get("expected_faq_ids")]
    unsupported_items = [it for it in eval_items if not it.get("expected_faq_ids")]

    recall_sums = {k: 0.0 for k in k_values}
    prec_sums = {k: 0.0 for k in k_values}
    ndcg_sums = {k: 0.0 for k in k_values}
    rr_sum = 0.0
    empty_count = 0

    for it in eval_items:
        retrieved = it.get("retrieved_faq_ids", [])
        if not retrieved:
            empty_count += 1

    for it in supported_items:
        retrieved = it.get("retrieved_faq_ids", [])
        expected = it.get("expected_faq_ids", [])

        for k in k_values:
            recall_sums[k] += compute_recall_at_k(retrieved, expected, k)
            prec_sums[k] += compute_precision_at_k(retrieved, expected, k)
            ndcg_sums[k] += compute_ndcg_at_k(retrieved, expected, k)

        rr_sum += compute_reciprocal_rank(retrieved, expected)

    n_sup = len(supported_items) if supported_items else 1
    n_tot = len(eval_items)

    result = {
        "total_queries": n_tot,
        "supported_queries": len(supported_items),
        "unsupported_queries": len(unsupported_items),
        "recall": {f"recall@{k}": round(recall_sums[k] / n_sup, 4) for k in k_values},
        "precision": {f"precision@{k}": round(prec_sums[k] / n_sup, 4) for k in k_values},
        "mrr": round(rr_sum / n_sup, 4),
        "ndcg": {f"ndcg@{k}": round(ndcg_sums[k] / n_sup, 4) for k in k_values},
        "empty_retrieval_rate": round(empty_count / n_tot, 4) if n_tot else 0.0,
    }

    return result


# ---------------------------------------------------------------------------
# Grounding & Citation Validation Metrics
# ---------------------------------------------------------------------------

def evaluate_citations_and_grounding(
    eval_records: Sequence[Dict[str, Any]],
    valid_faq_ids: Set[str],
) -> Dict[str, Any]:
    """
    Evaluate response grounding and citation integrity:
    1. Citation ID Validity: Do all cited IDs exist in the canonical knowledge base?
    2. Retrieval Membership: Were cited IDs present in retrieved_sources?
    3. Hallucinated / Fabricated Citations: IDs cited but never retrieved.
    4. Abstention Accuracy: Did the model abstain or avoid citing FAQs when no relevant FAQ exists?
    5. Clean separation of retrieved_sources vs used_sources.
    """
    total_responses = len(eval_records)
    total_citations_emitted = 0
    valid_id_count = 0
    in_retrieved_count = 0
    fabrication_count = 0
    correct_abstentions = 0
    unsupported_query_count = 0

    for rec in eval_records:
        retrieved_ids = {str(src.get("faq_id", "")).strip().upper() for src in rec.get("retrieved_sources", [])}
        used_sources = rec.get("used_sources", [])
        expected_faqs = rec.get("expected_faq_ids", [])
        response_text = rec.get("final_response", "")

        is_unsupported = len(expected_faqs) == 0
        if is_unsupported:
            unsupported_query_count += 1
            # Abstention is correct if no citations were used and response indicates review/unverified
            if len(used_sources) == 0:
                correct_abstentions += 1

        for src in used_sources:
            cid = str(src.get("faq_id", "")).strip().upper()
            total_citations_emitted += 1

            if cid in valid_faq_ids:
                valid_id_count += 1
            else:
                fabrication_count += 1

            if cid in retrieved_ids:
                in_retrieved_count += 1
            else:
                fabrication_count += 1

    validity_rate = (valid_id_count / total_citations_emitted) if total_citations_emitted else 1.0
    membership_rate = (in_retrieved_count / total_citations_emitted) if total_citations_emitted else 1.0
    abstention_rate = (correct_abstentions / unsupported_query_count) if unsupported_query_count else 1.0

    return {
        "total_responses_evaluated": total_responses,
        "total_citations_emitted": total_citations_emitted,
        "valid_citation_ids_count": valid_id_count,
        "citation_validity_rate": round(validity_rate, 4),
        "retrieval_membership_count": in_retrieved_count,
        "retrieval_membership_rate": round(membership_rate, 4),
        "fabricated_citation_count": fabrication_count,
        "unsupported_inquiries_count": unsupported_query_count,
        "correct_abstention_count": correct_abstentions,
        "abstention_accuracy_rate": round(abstention_rate, 4),
    }


# ---------------------------------------------------------------------------
# Latency Summary Metrics
# ---------------------------------------------------------------------------

def compute_latency_summary(latencies_ms: Sequence[float]) -> Dict[str, float]:
    """
    Compute statistically sound latency percentiles (mean, P50/median, P95, P99).
    """
    if not latencies_ms:
        return {"mean": 0.0, "median": 0.0, "p95": 0.0, "p99": 0.0, "sample_count": 0}

    arr = np.array(latencies_ms, dtype=float)
    return {
        "mean": round(float(np.mean(arr)), 2),
        "median": round(float(np.median(arr)), 2),
        "p95": round(float(np.percentile(arr, 95)), 2),
        "p99": round(float(np.percentile(arr, 99)), 2),
        "sample_count": len(arr),
    }
