"""
Tests for the complete end-to-end workflow pipeline.
"""
import unittest
from app.graph.workflow import run_ticket_workflow
from app.models.schemas import TicketState


class TestWorkflow(unittest.TestCase):

    def test_run_ticket_workflow_with_ticket_state(self):
        initial_state = TicketState(
            customer_name="John Doe",
            customer_id="CUST-456",
            email="john@example.com",
            tier="Platinum",
            subject="Payment deducted twice, please refund immediately",
        )

        result = run_ticket_workflow(initial_state)

        self.assertIsInstance(result, TicketState)
        self.assertIsNotNone(result.ticket_id)
        self.assertTrue(result.ticket_id.startswith("TKT-"))
        self.assertEqual(result.topic, "billing")
        self.assertEqual(result.sentiment, "NEGATIVE")
        self.assertEqual(result.priority, "High")
        self.assertEqual(result.routed_to, "Finance Team")
        self.assertEqual(result.escalation, "Escalated to Senior Manager")
        self.assertIsNotNone(result.final_response)
        self.assertIn(result.ticket_id, result.final_response)

    def test_run_ticket_workflow_with_dict(self):
        initial_dict = {
            "subject": "Need invoice copy for my records",
            "tier": "Silver",
        }

        result = run_ticket_workflow(initial_dict)

        self.assertIsInstance(result, TicketState)
        self.assertIsNotNone(result.ticket_id)
        self.assertEqual(result.topic, "billing")
        self.assertEqual(result.sentiment, "POSITIVE")
        # Silver (2) * POSITIVE (1) = 2 -> Low
        self.assertEqual(result.priority, "Low")
        self.assertEqual(result.routed_to, "Finance Team")
        self.assertEqual(result.escalation, "No Escalation Required")
        # Ensure dictionary-like access still works
        self.assertEqual(result["ticket_id"], result.ticket_id)
        self.assertEqual(result.get("priority"), "Low")


if __name__ == "__main__":
    unittest.main()
