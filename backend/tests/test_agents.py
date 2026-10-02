"""
Tests for individual agents.
"""
import unittest
from app.models.schemas import TicketState
from app.agents.classification import classification_agent
from app.agents.priority import priority_agent
from app.agents.routing import routing_agent
from app.agents.escalation import escalation_agent
from app.agents.response import response_agent


class TestAgents(unittest.TestCase):

    def test_classification_agent(self):
        state = TicketState(subject="Charged twice for my monthly bill", tier="Gold")
        result = classification_agent(state)

        self.assertIsNotNone(result.ticket_id)
        self.assertTrue(result.ticket_id.startswith("TKT-"))
        self.assertEqual(result.topic, "billing")
        self.assertIn(result.sentiment, ["POSITIVE", "NEGATIVE"])

    def test_priority_agent_calculation(self):
        # Platinum + NEGATIVE = 4 * 2 = 8 -> High
        state_plat_neg = TicketState(subject="Broken device", tier="Platinum", sentiment="NEGATIVE")
        result = priority_agent(state_plat_neg)
        self.assertEqual(result.priority, "High")

        # Gold + POSITIVE = 3 * 1 = 3 -> Medium
        state_gold_pos = TicketState(subject="Billing inquiry", tier="Gold", sentiment="POSITIVE")
        result = priority_agent(state_gold_pos)
        self.assertEqual(result.priority, "Medium")

        # Bronze + POSITIVE = 1 * 1 = 1 -> Low
        state_bronze_pos = TicketState(subject="General question", tier="Bronze", sentiment="POSITIVE")
        result = priority_agent(state_bronze_pos)
        self.assertEqual(result.priority, "Low")

    def test_routing_agent_mapping(self):
        # Billing -> Finance Team
        state = TicketState(subject="Test", topic="billing")
        self.assertEqual(routing_agent(state).routed_to, "Finance Team")

        # Shipping -> Logistics Team
        state = TicketState(subject="Test", topic="shipping")
        self.assertEqual(routing_agent(state).routed_to, "Logistics Team")

        # Technical -> Tech Support
        state = TicketState(subject="Test", topic="technical")
        self.assertEqual(routing_agent(state).routed_to, "Tech Support")

        # Other / Unknown -> General Support
        state = TicketState(subject="Test", topic="other")
        self.assertEqual(routing_agent(state).routed_to, "General Support")

    def test_escalation_agent(self):
        # High Priority + Platinum -> Escalated to Senior Manager
        state_plat_high = TicketState(subject="Test", tier="Platinum", priority="High")
        self.assertEqual(escalation_agent(state_plat_high).escalation, "Escalated to Senior Manager")

        # High Priority + Gold -> Escalated to Senior Manager
        state_gold_high = TicketState(subject="Test", tier="Gold", priority="High")
        self.assertEqual(escalation_agent(state_gold_high).escalation, "Escalated to Senior Manager")

        # High Priority + Silver -> No Escalation Required
        state_silver_high = TicketState(subject="Test", tier="Silver", priority="High")
        self.assertEqual(escalation_agent(state_silver_high).escalation, "No Escalation Required")

        # Medium Priority + Platinum -> No Escalation Required
        state_plat_med = TicketState(subject="Test", tier="Platinum", priority="Medium")
        self.assertEqual(escalation_agent(state_plat_med).escalation, "No Escalation Required")

    def test_response_agent(self):
        state = TicketState(
            subject="Invoice inquiry",
            ticket_id="TKT-20260929-TEST01",
            topic="billing",
            priority="Medium",
            routed_to="Finance Team",
            escalation="No Escalation Required",
        )
        result = response_agent(state)
        self.assertIn("TKT-20260929-TEST01", result.final_response)
        self.assertIn("Billing", result.final_response)
        self.assertIn("Finance Team", result.final_response)
        self.assertIn("No Escalation Required", result.final_response)


if __name__ == "__main__":
    unittest.main()
