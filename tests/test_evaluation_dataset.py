"""
Unit tests for Week 3 evaluation dataset schema, integrity, and data leakage checks.
"""
import json
from pathlib import Path
import unittest
import pandas as pd

from eval.build_week3_dataset import (
    OUTPUT_DATASET_PATH,
    TRAIN_CSV_PATH,
    TEST_CSV_PATH,
    compute_ground_truth_priority,
    compute_ground_truth_team,
    compute_ground_truth_escalation,
    check_leakage_against_training,
)


class TestEvaluationDataset(unittest.TestCase):
    """Test suite for evaluation dataset integrity and quality controls."""

    def setUp(self):
        self.assertTrue(OUTPUT_DATASET_PATH.exists(), "Evaluation dataset file must exist.")
        with open(OUTPUT_DATASET_PATH, "r", encoding="utf-8") as f:
            self.dataset = json.load(f)

    def test_dataset_size_and_schema(self):
        """Verify dataset contains >= 100 records (target 160) with valid schema."""
        self.assertGreaterEqual(len(self.dataset), 100)
        self.assertEqual(len(self.dataset), 160)

        required_keys = {
            "ticket_id",
            "ticket_text",
            "customer_tier",
            "expected_topic",
            "expected_sentiment",
            "expected_priority",
            "expected_team",
            "expected_escalation",
            "expected_faq_ids",
            "expected_resolution_facts",
            "requires_fallback",
            "requires_human_review",
            "split",
        }

        for record in self.dataset:
            missing = required_keys - record.keys()
            self.assertEqual(len(missing), 0, f"Record {record.get('ticket_id')} missing keys: {missing}")
            self.assertTrue(record["ticket_text"].strip(), "Ticket text must not be empty.")
            self.assertIn(record["expected_topic"], ["billing", "shipping", "technical", "other"])
            self.assertIn(record["expected_sentiment"], ["POSITIVE", "NEGATIVE"])
            self.assertIn(record["customer_tier"], ["Platinum", "Gold", "Silver", "Bronze"])
            self.assertIn(record["expected_priority"], ["High", "Medium", "Low"])
            self.assertIn(record["split"], ["val", "test"])

    def test_topic_distribution_balance(self):
        """Verify balanced category representation across all four topics."""
        topic_counts = {}
        for r in self.dataset:
            topic_counts[r["expected_topic"]] = topic_counts.get(r["expected_topic"], 0) + 1

        for topic in ["billing", "shipping", "technical", "other"]:
            self.assertEqual(topic_counts[topic], 40, f"Topic '{topic}' should have 40 samples.")

    def test_split_stratification(self):
        """Verify proper validation / held-out test split."""
        val_count = sum(1 for r in self.dataset if r["split"] == "val")
        test_count = sum(1 for r in self.dataset if r["split"] == "test")

        self.assertEqual(val_count, 60)
        self.assertEqual(test_count, 100)

    def test_zero_data_leakage(self):
        """Verify strict zero leakage against train.csv and test.csv."""
        leakage = check_leakage_against_training(self.dataset)
        self.assertFalse(leakage["has_leakage"], f"Found data leakage: {leakage}")
        self.assertEqual(leakage["train_overlap_count"], 0)
        self.assertEqual(leakage["test_overlap_count"], 0)

    def test_ground_truth_business_rules(self):
        """Verify ground-truth labels strictly adhere to production business rules."""
        for r in self.dataset:
            exp_prio = compute_ground_truth_priority(r["customer_tier"], r["expected_sentiment"])
            exp_team = compute_ground_truth_team(r["expected_topic"])
            exp_esc = compute_ground_truth_escalation(r["customer_tier"], exp_prio)

            self.assertEqual(r["expected_priority"], exp_prio)
            self.assertEqual(r["expected_team"], exp_team)
            self.assertEqual(r["expected_escalation"], exp_esc)


if __name__ == "__main__":
    unittest.main()
