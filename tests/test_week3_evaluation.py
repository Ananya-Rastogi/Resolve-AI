"""
Comprehensive Week 3 Test Suite for Evaluation, Quality Engineering,
Regression Protection, and Backward Compatibility.
"""
import json
from pathlib import Path
import unittest

from app.models.schemas import CustomerTier, TicketPriority, TicketState
from app.agents.priority import priority_agent
from app.agents.routing import routing_agent, ROUTING_MAP
from app.agents.escalation import escalation_agent
from app.agents.response import extract_used_sources, response_agent
from app.agents.llm_client import MockLLMClient, LLMAPIError
from app.graph.workflow import run_ticket_workflow, DEFAULT_CONFIDENCE_THRESHOLD
from eval.metrics import compute_classification_metrics, evaluate_citations_and_grounding


BASE_DIR = Path(__file__).resolve().parent.parent


class TestWeek3Evaluation(unittest.TestCase):
    """Week 3 Quality Engineering & Verification Test Suite."""

    def test_01_all_evaluation_artifacts_exist_and_valid(self):
        """1. Verify that all 5 required Week 3 evaluation artifacts exist and contain valid data."""
        artifacts = {
            "classification_eval.json": BASE_DIR / "eval" / "classification_eval.json",
            "rag_eval.json": BASE_DIR / "eval" / "rag_eval.json",
            "end_to_end_eval.json": BASE_DIR / "eval" / "end_to_end_eval.json",
            "evaluation_summary.json": BASE_DIR / "eval" / "evaluation_summary.json",
            "evaluation_report.md": BASE_DIR / "eval" / "evaluation_report.md",
        }

        for name, path in artifacts.items():
            self.assertTrue(path.exists(), f"Artifact {name} must exist at {path}")
            self.assertGreater(path.stat().st_size, 100, f"Artifact {name} must not be empty")

            if name.endswith(".json"):
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.assertIsInstance(data, (dict, list), f"{name} must contain valid JSON")

    def test_02_topic_to_team_routing_independent_of_llm(self):
        """2. Verify every supported topic-to-team mapping and boundary cases."""
        expected_mappings = {
            "billing": "Finance Team",
            "shipping": "Logistics Team",
            "technical": "Tech Support",
            "other": "General Support",
            "unknown_topic": "General Support",
            "": "General Support",
            None: "General Support",
        }

        for topic, expected_team in expected_mappings.items():
            state = TicketState(subject="Test routing inquiry", topic=topic)
            updated = routing_agent(state)
            self.assertEqual(
                updated.routed_to,
                expected_team,
                f"Topic '{topic}' should route to '{expected_team}', got '{updated.routed_to}'"
            )

    def test_03_priority_calculation_rules(self):
        """3. Verify high, medium, and low priority rules across all tiers and sentiments."""
        test_cases = [
            # Platinum: Score 4 * weight (2 for NEG, 1 for POS)
            ("Platinum", "NEGATIVE", "High"),   # 8 >= 6
            ("Platinum", "POSITIVE", "Medium"), # 4 >= 3
            # Gold: Score 3 * weight
            ("Gold", "NEGATIVE", "High"),       # 6 >= 6
            ("Gold", "POSITIVE", "Medium"),     # 3 >= 3
            # Silver: Score 2 * weight
            ("Silver", "NEGATIVE", "Medium"),   # 4 >= 3
            ("Silver", "POSITIVE", "Low"),      # 2 < 3
            # Bronze: Score 1 * weight
            ("Bronze", "NEGATIVE", "Low"),      # 2 < 3
            ("Bronze", "POSITIVE", "Low"),      # 1 < 3
        ]

        for tier, sentiment, expected_prio in test_cases:
            state = TicketState(subject="Test priority", tier=tier, sentiment=sentiment)
            updated = priority_agent(state)
            self.assertEqual(
                updated.priority,
                expected_prio,
                f"Tier {tier} + Sentiment {sentiment} should yield Priority {expected_prio}, got {updated.priority}"
            )

    def test_04_escalation_rules(self):
        """4. Verify escalation occurs strictly for High priority Platinum/Gold accounts."""
        test_cases = [
            ("Platinum", "High", "Escalated to Senior Manager"),
            ("Gold", "High", "Escalated to Senior Manager"),
            ("Silver", "High", "No Escalation Required"),
            ("Bronze", "High", "No Escalation Required"),
            ("Platinum", "Medium", "No Escalation Required"),
            ("Gold", "Low", "No Escalation Required"),
        ]

        for tier, priority, expected_esc in test_cases:
            state = TicketState(subject="Test escalation", tier=tier, priority=priority)
            updated = escalation_agent(state)
            self.assertEqual(
                updated.escalation,
                expected_esc,
                f"Tier {tier} + Priority {priority} should yield '{expected_esc}', got '{updated.escalation}'"
            )

    def test_05_threshold_sweep_integrity_and_default(self):
        """5. Verify threshold sweep contains expected points and keeps 0.50 default."""
        with open(BASE_DIR / "eval" / "classification_eval.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        sweep = data["validation_threshold_sweep"]
        threshold_vals = [s["threshold"] for s in sweep]
        self.assertEqual(threshold_vals, [0.4, 0.5, 0.6, 0.7, 0.8])
        self.assertEqual(data["selected_production_threshold"], DEFAULT_CONFIDENCE_THRESHOLD)

    def test_06_rag_benchmark_metrics_targets(self):
        """6. Verify RAG retrieval satisfies core accuracy benchmarks on canonical FAQs."""
        with open(BASE_DIR / "eval" / "rag_eval.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        hyb = data["strategy_comparison"]["hybrid_category_with_fallback"]
        r1 = hyb["recall"]["recall@1"]
        r3 = hyb["recall"]["recall@3"]
        r5 = hyb["recall"]["recall@5"]
        mrr = hyb["mrr"]

        self.assertGreaterEqual(r1, 0.70, f"Recall@1 should be >= 70%, got {r1 * 100:.1f}%")
        self.assertGreaterEqual(r3, 0.85, f"Recall@3 should be >= 85%, got {r3 * 100:.1f}%")
        self.assertGreaterEqual(r5, 0.90, f"Recall@5 should be >= 90%, got {r5 * 100:.1f}%")
        self.assertGreaterEqual(mrr, 0.80, f"MRR should be >= 0.80, got {mrr:.4f}")

    def test_07_citation_integrity_and_fabrication_rejection(self):
        """7. Verify citation validation rejects fabricated and unretrieved IDs."""
        retrieved = [
            {"faq_id": "FAQ_001", "category": "Payment_Issue", "score": 0.55},
            {"faq_id": "FAQ_025", "category": "Payment_Issue", "score": 0.32},
        ]

        # Case 1: Real retrieved source cited
        resp_valid = "You can pay with major cards as stated in FAQ_001."
        used_valid = extract_used_sources(resp_valid, retrieved)
        self.assertEqual(len(used_valid), 1)
        self.assertEqual(used_valid[0]["faq_id"], "FAQ_001")

        # Case 2: Hallucinated / external citation rejected
        resp_fake = "Refer to FAQ_999 for special promotions."
        used_fake = extract_used_sources(resp_fake, retrieved)
        self.assertEqual(len(used_fake), 0)

        # Case 3: Real FAQ ID that was NOT in retrieved sources rejected
        resp_unretrieved = "Refer to FAQ_010 for duplicate charges."
        used_unretrieved = extract_used_sources(resp_unretrieved, retrieved)
        self.assertEqual(len(used_unretrieved), 0)

    def test_08_abstention_on_unsupported_inquiries(self):
        """8. Verify system abstains when knowledge base cannot answer inquiry."""
        state = TicketState(
            subject="Can I pay using Bitcoin cryptocurrency or Dogecoin?",
            customer_name="Crypto User",
            email="crypto@example.com",
            tier=CustomerTier.BRONZE,
        )
        result = run_ticket_workflow(state)

        # System should not cite FAQs for unsupported cryptocurrency payment
        self.assertEqual(len(result.used_sources), 0)
        self.assertIn("could not be found", result.final_response.lower())

    def test_09_offline_graceful_degradation_on_llm_failure(self):
        """9. Verify workflow operates safely with fallback when LLM encounters errors."""
        failing_mock = MockLLMClient(always_fail=True)
        state = TicketState(
            subject="invoice question",
            tier=CustomerTier.SILVER,
        )

        # Execute response_agent directly with failing mock
        res_state = response_agent(state, client=failing_mock)
        self.assertIsNotNone(res_state.final_response)
        self.assertIn("Customer", res_state.final_response)

    def test_10_backward_compatibility_end_to_end(self):
        """10. Verify full end-to-end LangGraph pipeline with dictionary and TicketState input."""
        dict_input = {
            "customer_name": "Bob Vance",
            "customer_email": "bob@vance.com",
            "tier": "Gold",
            "subject": "I was billed twice for my order ORD-4412",
        }
        res_dict = run_ticket_workflow(dict_input)
        self.assertEqual(res_dict.routed_to, "Finance Team")
        self.assertIn("FAQ_010", [s["faq_id"] for s in res_dict.retrieved_sources])

        typed_input = TicketState(
            customer_name="Pam Beesly",
            email="pam@dunder.com",
            tier=CustomerTier.PLATINUM,
            subject="Where is my shipment tracking link?",
        )
        res_typed = run_ticket_workflow(typed_input)
        self.assertEqual(res_typed.routed_to, "Logistics Team")
        self.assertIsNotNone(res_typed.final_response)


if __name__ == "__main__":
    unittest.main()
