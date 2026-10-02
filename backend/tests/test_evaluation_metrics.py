"""
Unit tests for core evaluation metrics calculation.
Validates classification, retrieval (Recall@K, Precision@K, MRR, nDCG@K),
citation validity, and latency percentiles on known hand-calculated cases.
"""
import unittest
import numpy as np

from eval.metrics import (
    compute_classification_metrics,
    compute_recall_at_k,
    compute_precision_at_k,
    compute_reciprocal_rank,
    compute_ndcg_at_k,
    aggregate_retrieval_metrics,
    evaluate_citations_and_grounding,
    compute_latency_summary,
)


class TestEvaluationMetrics(unittest.TestCase):
    """Test suite verifying mathematical correctness of all evaluation metrics."""

    def test_classification_metrics_hand_calculated(self):
        """Verify multi-class accuracy, precision, recall, and F1 on known example."""
        y_true = ["billing", "billing", "shipping", "technical"]
        y_pred = ["billing", "shipping", "shipping", "technical"]

        res = compute_classification_metrics(y_true, y_pred)
        # 3 out of 4 correct -> Accuracy = 0.75
        self.assertEqual(res["accuracy"], 0.75)
        self.assertEqual(res["sample_count"], 4)

        # Billing: true=2, pred=1 (1 correct) -> prec=1/1=1.0, rec=1/2=0.5, f1=2*(1*0.5)/(1.5)=0.6667
        self.assertAlmostEqual(res["per_class"]["billing"]["precision"], 1.0, places=3)
        self.assertAlmostEqual(res["per_class"]["billing"]["recall"], 0.5, places=3)

        # Technical: true=1, pred=1 -> prec=1.0, rec=1.0, f1=1.0
        self.assertAlmostEqual(res["per_class"]["technical"]["f1"], 1.0, places=3)

    def test_retrieval_recall_and_precision_at_k(self):
        """Verify Recall@K and Precision@K calculations."""
        retrieved = ["FAQ_001", "FAQ_002", "FAQ_003"]
        expected = ["FAQ_002"]

        # Recall@K
        self.assertEqual(compute_recall_at_k(retrieved, expected, k=1), 0.0)
        self.assertEqual(compute_recall_at_k(retrieved, expected, k=2), 1.0)
        self.assertEqual(compute_recall_at_k(retrieved, expected, k=3), 1.0)

        # Precision@K
        self.assertEqual(compute_precision_at_k(retrieved, expected, k=1), 0.0)
        self.assertEqual(compute_precision_at_k(retrieved, expected, k=2), 0.5)
        self.assertAlmostEqual(compute_precision_at_k(retrieved, expected, k=3), 1.0 / 3.0, places=3)

    def test_reciprocal_rank(self):
        """Verify Mean Reciprocal Rank element calculations."""
        # Top-1 hit
        self.assertEqual(compute_reciprocal_rank(["FAQ_010", "FAQ_020"], ["FAQ_010"]), 1.0)
        # Top-2 hit
        self.assertEqual(compute_reciprocal_rank(["FAQ_020", "FAQ_010"], ["FAQ_010"]), 0.5)
        # Top-3 hit
        self.assertAlmostEqual(compute_reciprocal_rank(["FAQ_001", "FAQ_002", "FAQ_010"], ["FAQ_010"]), 1.0 / 3.0, places=4)
        # Miss
        self.assertEqual(compute_reciprocal_rank(["FAQ_001", "FAQ_002"], ["FAQ_010"]), 0.0)

    def test_ndcg_at_k(self):
        """Verify nDCG@K with ideal and sub-optimal rankings."""
        # Rank 1 hit: DCG = 1 / log2(2) = 1.0, IDCG = 1.0 -> nDCG = 1.0
        ndcg_top1 = compute_ndcg_at_k(["FAQ_001", "FAQ_002"], ["FAQ_001"], k=2)
        self.assertAlmostEqual(ndcg_top1, 1.0, places=4)

        # Rank 2 hit: DCG = 1 / log2(3) = 0.6309, IDCG = 1 / log2(2) = 1.0 -> nDCG = 0.6309
        ndcg_top2 = compute_ndcg_at_k(["FAQ_002", "FAQ_001"], ["FAQ_001"], k=2)
        self.assertAlmostEqual(ndcg_top2, 0.6309, places=3)

        # Completely irrelevant -> nDCG = 0.0
        ndcg_miss = compute_ndcg_at_k(["FAQ_003", "FAQ_004"], ["FAQ_001"], k=2)
        self.assertEqual(ndcg_miss, 0.0)

    def test_citation_evaluation_and_fabrication_detection(self):
        """Verify detection of fabricated citation IDs and non-retrieved citations."""
        canonical_ids = {"FAQ_001", "FAQ_002", "FAQ_003"}

        # Valid citation case
        records_valid = [{
            "retrieved_sources": [{"faq_id": "FAQ_001"}],
            "used_sources": [{"faq_id": "FAQ_001"}],
            "expected_faq_ids": ["FAQ_001"],
            "final_response": "Based on FAQ_001, here is your answer.",
        }]
        res_valid = evaluate_citations_and_grounding(records_valid, canonical_ids)
        self.assertEqual(res_valid["citation_validity_rate"], 1.0)
        self.assertEqual(res_valid["retrieval_membership_rate"], 1.0)
        self.assertEqual(res_valid["fabricated_citation_count"], 0)

        # Fabricated ID case (does not exist in knowledge base)
        records_fake_id = [{
            "retrieved_sources": [{"faq_id": "FAQ_001"}],
            "used_sources": [{"faq_id": "FAQ_999"}],
            "expected_faq_ids": ["FAQ_001"],
            "final_response": "Based on FAQ_999.",
        }]
        res_fake = evaluate_citations_and_grounding(records_fake_id, canonical_ids)
        self.assertEqual(res_fake["citation_validity_rate"], 0.0)
        self.assertGreater(res_fake["fabricated_citation_count"], 0)

        # Non-membership case (real FAQ_002, but was never retrieved for this ticket)
        records_unretrieved = [{
            "retrieved_sources": [{"faq_id": "FAQ_001"}],
            "used_sources": [{"faq_id": "FAQ_002"}],
            "expected_faq_ids": ["FAQ_001"],
            "final_response": "Based on FAQ_002.",
        }]
        res_unretrieved = evaluate_citations_and_grounding(records_unretrieved, canonical_ids)
        self.assertEqual(res_unretrieved["retrieval_membership_rate"], 0.0)

    def test_latency_summary(self):
        """Verify latency statistics percentiles calculation."""
        latencies = [10.0, 20.0, 30.0, 40.0, 50.0]
        summary = compute_latency_summary(latencies)
        self.assertEqual(summary["mean"], 30.0)
        self.assertEqual(summary["median"], 30.0)
        self.assertEqual(summary["sample_count"], 5)


if __name__ == "__main__":
    unittest.main()
