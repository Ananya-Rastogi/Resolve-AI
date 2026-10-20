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

    def test_ticket_event_schema_uuid_string_id(self):
        """Verify TicketEventSchema accepts UUID string as event ID (Supabase production)."""
        from app.api.schemas import TicketEventSchema

        uuid_str = "87824b75-367b-49fd-bb8c-b36189e8df6b"
        event = TicketEventSchema(
            id=uuid_str,
            ticket_id="TKT-20261020-001",
            event_type="ticket_created",
            actor="system",
            details={"action": "ticket_created"},
            created_at="2026-10-20T16:23:39.449612+00:00",
        )
        self.assertEqual(event.id, uuid_str)
        dumped = event.model_dump(mode="json")
        self.assertEqual(dumped["id"], uuid_str)

    def test_ticket_event_schema_integer_id(self):
        """Verify TicketEventSchema accepts integer as event ID (SQLite development/tests)."""
        from app.api.schemas import TicketEventSchema

        event = TicketEventSchema(
            id=42,
            ticket_id="TKT-20261020-002",
            event_type="ticket_updated",
            actor="agent",
            details={"action": "escalated"},
            created_at="2026-10-20T16:25:00Z",
        )
        self.assertEqual(event.id, 42)
        dumped = event.model_dump(mode="json")
        self.assertEqual(dumped["id"], 42)

    def test_ticket_event_schema_uuid_object_coercion(self):
        """Verify TicketEventSchema coerces uuid.UUID objects to strings without failing."""
        import uuid
        from app.api.schemas import TicketEventSchema

        u = uuid.uuid4()
        event = TicketEventSchema(
            id=u,
            ticket_id="TKT-20261020-003",
            event_type="ticket_created",
            created_at="2026-10-20T16:26:00Z",
        )
        self.assertEqual(event.id, str(u))

    def test_ticket_event_schema_details_and_datetime_resilience(self):
        """Verify TicketEventSchema handles JSON string details and datetime objects seamlessly."""
        from datetime import datetime, timezone
        from app.api.schemas import TicketEventSchema

        now = datetime.now(timezone.utc)
        event = TicketEventSchema(
            id="123e4567-e89b-12d3-a456-426614174000",
            ticket_id="TKT-20261020-004",
            event_type="ticket_created",
            details='{"key": "value"}',
            created_at=now,
        )
        self.assertEqual(event.details, {"key": "value"})
        self.assertEqual(event.created_at, now.isoformat())


if __name__ == "__main__":
    unittest.main()

