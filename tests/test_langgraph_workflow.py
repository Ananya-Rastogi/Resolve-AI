"""
Unit and integration tests for Week 1 LangGraph migration, hybrid classification,
conditional routing, structured LLM validation, retries, and fallback handling.
"""
import os
import unittest
from unittest.mock import patch

from app.models.schemas import TicketState, LLMClassificationOutput
from app.agents.llm_client import MockLLMClient, LLMValidationError, LLMAPIError
from app.agents.llm_classification import llm_classification_agent
from app.graph.workflow import (
    run_ticket_workflow,
    create_ticket_graph,
    route_after_classification,
)


class TestLangGraphWorkflow(unittest.TestCase):

    def setUp(self):
        # Default mock environment
        self.mock_client = MockLLMClient(default_topic="technical", default_sentiment="NEGATIVE")

    def test_1_high_confidence_bypasses_llm(self):
        """1. High-confidence ML prediction bypasses LLM."""
        state = TicketState(
            subject="charged twice for same order",
            tier="Platinum",
        )
        # Threshold set low so ML confidence clearly exceeds it
        with patch.dict(os.environ, {"CLASSIFICATION_CONFIDENCE_THRESHOLD": "0.30"}):
            result = run_ticket_workflow(state)

        self.assertFalse(result.llm_called)
        self.assertEqual(result.classification_source, "ml")
        self.assertIsNotNone(result.ml_confidence)
        self.assertGreaterEqual(result.ml_confidence, 0.30)
        self.assertEqual(result.topic, "billing")

    def test_2_low_confidence_routes_to_llm(self):
        """2. Low-confidence prediction routes to LLM."""
        state = TicketState(
            subject="vague ambiguous support request",
            tier="Gold",
        )
        # Force threshold higher than ML probability
        with patch.dict(os.environ, {"CLASSIFICATION_CONFIDENCE_THRESHOLD": "0.99"}):
            with patch("app.agents.llm_classification.get_llm_client", return_value=self.mock_client):
                result = run_ticket_workflow(state)

        self.assertTrue(result.llm_called)
        self.assertEqual(result.classification_source, "llm")
        self.assertTrue(result.llm_succeeded)
        self.assertFalse(result.fallback_occurred)

    def test_3_llm_structured_output_validated(self):
        """3. LLM structured output is strictly validated against Pydantic schema."""
        valid_data = {
            "topic": "technical",
            "sentiment": "NEGATIVE",
            "urgency": "critical",
            "extracted_order_id": "ORD-9876",
        }
        output = LLMClassificationOutput.model_validate(valid_data)
        self.assertEqual(output.topic, "technical")
        self.assertEqual(output.urgency, "critical")
        self.assertEqual(output.extracted_order_id, "ORD-9876")

        # Invalid topic must raise ValidationError
        with self.assertRaises(Exception):
            LLMClassificationOutput.model_validate({"topic": "arbitrary_topic", "sentiment": "NEGATIVE"})

        # Invalid sentiment must raise ValidationError
        with self.assertRaises(Exception):
            LLMClassificationOutput.model_validate({"topic": "billing", "sentiment": "NEUTRAL"})

    def test_4_invalid_llm_output_triggers_retry(self):
        """4. Invalid LLM output triggers retry; recovers if transient."""
        # 1 initial failure + 1 retry = 2 attempts, then succeeds on 2nd attempt
        client = MockLLMClient(fail_count=1)
        state = TicketState(subject="payment clarification needed", tier="Silver")
        state.ml_topic = "billing"
        state.ml_sentiment = "POSITIVE"
        state.ml_confidence = 0.50

        result = llm_classification_agent(state, client=client)

        self.assertEqual(client.call_count, 2)
        self.assertTrue(result.llm_succeeded)
        self.assertEqual(result.classification_source, "llm")

    def test_5_llm_failure_eventually_falls_back_to_ml(self):
        """5. LLM failure eventually falls back to ML after retries are exhausted."""
        client = MockLLMClient(always_fail=True)
        state = TicketState(subject="package delayed shipping issue", tier="Bronze")
        state.ml_topic = "shipping"
        state.ml_sentiment = "NEGATIVE"
        state.ml_confidence = 0.65

        result = llm_classification_agent(state, client=client)

        # Max retries = 2 -> 3 total calls
        self.assertEqual(client.call_count, 3)
        self.assertFalse(result.llm_succeeded)
        self.assertTrue(result.fallback_occurred)
        self.assertEqual(result.classification_source, "ml_fallback")
        self.assertEqual(result.topic, "shipping")
        self.assertEqual(result.sentiment, "NEGATIVE")

    def test_6_classification_source_tracking(self):
        """6. classification_source accurately records 'ml', 'llm', or 'ml_fallback'."""
        # Case A: ML source
        with patch.dict(os.environ, {"CLASSIFICATION_CONFIDENCE_THRESHOLD": "0.10"}):
            res_ml = run_ticket_workflow({"subject": "refund request for order", "tier": "Gold"})
            self.assertEqual(res_ml.classification_source, "ml")

        # Case B: LLM source
        with patch.dict(os.environ, {"CLASSIFICATION_CONFIDENCE_THRESHOLD": "0.99"}):
            with patch("app.agents.llm_classification.get_llm_client", return_value=self.mock_client):
                res_llm = run_ticket_workflow({"subject": "app login crash", "tier": "Gold"})
                self.assertEqual(res_llm.classification_source, "llm")

        # Case C: ML Fallback source
        failing_client = MockLLMClient(always_fail=True)
        with patch.dict(os.environ, {"CLASSIFICATION_CONFIDENCE_THRESHOLD": "0.99"}):
            with patch("app.agents.llm_classification.get_llm_client", return_value=failing_client):
                res_fallback = run_ticket_workflow({"subject": "app login crash", "tier": "Gold"})
                self.assertEqual(res_fallback.classification_source, "ml_fallback")

    def test_7_existing_priority_logic_still_works(self):
        """7. Existing priority rules remain intact."""
        # High: Platinum (4) * NEGATIVE (2) = 8
        state_high = TicketState(subject="Broken device", tier="Platinum")
        state_high.sentiment = "NEGATIVE"
        with patch.dict(os.environ, {"CLASSIFICATION_CONFIDENCE_THRESHOLD": "0.10"}):
            res = run_ticket_workflow(state_high)
            self.assertEqual(res.priority, "High")

        # Low: Bronze (1) * POSITIVE (1) = 1
        state_low = TicketState(subject="General support inquiry", tier="Bronze")
        state_low.sentiment = "POSITIVE"
        with patch.dict(os.environ, {"CLASSIFICATION_CONFIDENCE_THRESHOLD": "0.10"}):
            res = run_ticket_workflow(state_low)
            self.assertEqual(res.priority, "Low")

    def test_8_existing_routing_logic_still_works(self):
        """8. Existing routing mapping remains intact."""
        with patch.dict(os.environ, {"CLASSIFICATION_CONFIDENCE_THRESHOLD": "0.10"}):
            res_billing = run_ticket_workflow({"subject": "invoice charge issue", "tier": "Gold"})
            self.assertEqual(res_billing.routed_to, "Finance Team")

            res_shipping = run_ticket_workflow({"subject": "order tracking delayed", "tier": "Gold"})
            self.assertEqual(res_shipping.routed_to, "Logistics Team")

    def test_9_existing_escalation_logic_still_works(self):
        """9. Existing escalation rules remain intact."""
        # High Priority + Platinum -> Escalated
        state_plat = TicketState(
            subject="refund not received charged twice",
            tier="Platinum",
        )
        with patch.dict(os.environ, {"CLASSIFICATION_CONFIDENCE_THRESHOLD": "0.10"}):
            res_plat = run_ticket_workflow(state_plat)
            self.assertEqual(res_plat.escalation, "Escalated to Senior Manager")

        # Low Priority + Platinum -> No Escalation
        state_plat_pos = TicketState(
            subject="thank you great service",
            tier="Platinum",
        )
        with patch.dict(os.environ, {"CLASSIFICATION_CONFIDENCE_THRESHOLD": "0.10"}):
            res_pos = run_ticket_workflow(state_plat_pos)
            self.assertEqual(res_pos.escalation, "No Escalation Required")

    def test_10_complete_langgraph_workflow_runs_successfully(self):
        """10. Complete LangGraph workflow runs end-to-end and generates response."""
        state = TicketState(
            customer_name="John Doe",
            customer_id="CUST-789",
            email="john@example.com",
            tier="Platinum",
            subject="Order not received, package delayed for order ORD-12345",
        )
        result = run_ticket_workflow(state)

        self.assertIsInstance(result, TicketState)
        self.assertTrue(result.ticket_id.startswith("TKT-"))
        self.assertIsNotNone(result.topic)
        self.assertIsNotNone(result.sentiment)
        self.assertIsNotNone(result.priority)
        self.assertIsNotNone(result.routed_to)
        self.assertIsNotNone(result.escalation)
        self.assertIsNotNone(result.final_response)
        self.assertIn(result.ticket_id, result.final_response)


if __name__ == "__main__":
    unittest.main()
