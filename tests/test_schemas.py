"""
Tests for TicketState schema and validation.
"""
import unittest
from app.models.schemas import TicketState, CustomerTier


class TestTicketSchemas(unittest.TestCase):

    def test_ticket_state_valid_creation(self):
        state = TicketState(
            customer_name="Alice",
            customer_id="CUST-101",
            email="alice@example.com",
            tier="Platinum",
            subject="Payment deducted twice for subscription",
        )
        self.assertEqual(state.customer_name, "Alice")
        self.assertEqual(state.tier, CustomerTier.PLATINUM.value)
        self.assertEqual(state.subject, "Payment deducted twice for subscription")
        self.assertIsNone(state.ticket_id)

    def test_ticket_state_empty_subject_validation(self):
        with self.assertRaises(ValueError):
            TicketState(subject="   ")

    def test_ticket_state_dict_compatibility(self):
        state = TicketState(subject="Network is completely down", tier="Gold")

        # Dict read access
        self.assertEqual(state["subject"], "Network is completely down")
        self.assertEqual(state.get("tier"), "Gold")
        self.assertEqual(state.get("non_existent", "default_val"), "default_val")

        # Dict write access
        state["priority"] = "High"
        self.assertEqual(state.priority, "High")
        self.assertEqual(state["priority"], "High")

    def test_ticket_state_alias_support(self):
        state = TicketState(
            issue_description="Cannot reset password",
            customer_tier="Silver",
            customer_email="user@test.com",
        )
        self.assertEqual(state.subject, "Cannot reset password")
        self.assertEqual(state.tier, "Silver")
        self.assertEqual(state.email, "user@test.com")


if __name__ == "__main__":
    unittest.main()
