"""
Integration tests for FastAPI backend endpoints.
"""
import unittest
from fastapi.testclient import TestClient

from app.api.main import app
from app.db.repository import SQLiteRepository, set_repository


class TestFastAPIBackend(unittest.TestCase):
    """Test suite covering health, ticket triage, queue listing, updates, and analytics."""

    @classmethod
    def setUpClass(cls):
        # Use isolated in-memory SQLite database for test suite
        cls.test_repo = SQLiteRepository(db_path=":memory:")
        set_repository(cls.test_repo)
        cls.client = TestClient(app)

    def test_01_health_endpoint(self):
        """Verify GET /api/health returns healthy status and metadata."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["storage_backend"], "local_sqlite")
        self.assertEqual(data["database_status"], "ok")

    def test_02_create_and_triage_ticket(self):
        """Verify POST /api/tickets triages through existing workflow and persists."""
        payload = {
            "subject": "I was charged twice on my credit card for invoice #INV-9021. Please issue a refund.",
            "customer_name": "Alice Tester",
            "customer_id": "CUST-001",
            "email": "alice@example.com",
            "tier": "Platinum",
            "idempotency_key": "IDEM-TEST-001",
        }
        response = self.client.post("/api/tickets", json=payload)
        self.assertEqual(response.status_code, 201)
        data = response.json()

        self.assertTrue(data["ticket_id"].startswith("TKT-"))
        self.assertEqual(data["customer_name"], "Alice Tester")
        self.assertEqual(data["category"], "billing")
        self.assertIn(data["sentiment"], ["POSITIVE", "NEGATIVE"])
        self.assertIn(data["priority"], ["High", "Medium", "Low"])
        self.assertEqual(data["assigned_team"], "Finance Team")
        self.assertIsNotNone(data["generated_reply"])
        self.assertIsNotNone(data.get("analysis"))
        self.assertGreaterEqual(len(data.get("events", [])), 1)

    def test_03_idempotency_deduplication(self):
        """Verify duplicate submission with same idempotency_key returns original ticket."""
        payload = {
            "subject": "Duplicate test inquiry",
            "customer_name": "Bob",
            "tier": "Gold",
            "idempotency_key": "IDEM-UNIQUE-KEY-999",
        }
        res1 = self.client.post("/api/tickets", json=payload)
        self.assertEqual(res1.status_code, 201)
        id1 = res1.json()["ticket_id"]

        # Submit again with same idempotency key
        res2 = self.client.post("/api/tickets", json=payload)
        self.assertEqual(res2.status_code, 200)
        id2 = res2.json()["ticket_id"]
        self.assertEqual(id1, id2)

    def test_04_create_validation_error(self):
        """Verify 422 returned on empty subject."""
        payload = {
            "subject": "   ",
            "tier": "Gold",
        }
        response = self.client.post("/api/tickets", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_05_list_tickets_and_filtering(self):
        """Verify GET /api/tickets supports pagination and query filters."""
        # Create a second ticket with shipping
        self.client.post(
            "/api/tickets",
            json={
                "subject": "Tracking link not working for my express parcel",
                "customer_name": "Charlie",
                "tier": "Silver",
            },
        )

        response = self.client.get("/api/tickets?page=1&limit=10")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(data["total"], 2)
        self.assertGreaterEqual(len(data["items"]), 2)

        # Filter by category=billing
        billing_res = self.client.get("/api/tickets?category=billing")
        self.assertEqual(billing_res.status_code, 200)
        billing_items = billing_res.json()["items"]
        self.assertTrue(all(item["category"] == "billing" for item in billing_items))

    def test_06_get_ticket_details(self):
        """Verify GET /api/tickets/{ticket_id} returns full analysis and audit history."""
        # Fetch first ticket
        list_res = self.client.get("/api/tickets?limit=1")
        ticket_id = list_res.json()["items"][0]["ticket_id"]

        detail_res = self.client.get(f"/api/tickets/{ticket_id}")
        self.assertEqual(detail_res.status_code, 200)
        detail = detail_res.json()
        self.assertEqual(detail["ticket_id"], ticket_id)
        self.assertIsNotNone(detail.get("analysis"))
        self.assertIsInstance(detail.get("events"), list)

    def test_07_get_ticket_not_found(self):
        """Verify GET /api/tickets/{non_existent} returns 404."""
        response = self.client.get("/api/tickets/TKT-DOES-NOT-EXIST")
        self.assertEqual(response.status_code, 404)

    def test_08_update_ticket(self):
        """Verify PATCH /api/tickets/{ticket_id} safely updates status and assigned team."""
        list_res = self.client.get("/api/tickets?limit=1")
        ticket_id = list_res.json()["items"][0]["ticket_id"]

        patch_res = self.client.patch(
            f"/api/tickets/{ticket_id}",
            json={"status": "resolved", "assigned_team": "Billing Support", "actor": "manager_alice"},
        )
        self.assertEqual(patch_res.status_code, 200)
        updated = patch_res.json()
        self.assertEqual(updated["status"], "resolved")

        # Verify audit event was logged
        detail_res = self.client.get(f"/api/tickets/{ticket_id}")
        events = detail_res.json().get("events", [])
        update_events = [e for e in events if e.get("event_type") == "ticket_updated"]
        self.assertGreaterEqual(len(update_events), 1)

    def test_09_analytics_endpoint(self):
        """Verify GET /api/analytics returns real aggregated statistics and offline evaluation benchmarks."""
        response = self.client.get("/api/analytics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("live_metrics", data)
        live = data["live_metrics"]
        self.assertIn("total_tickets", live)
        self.assertGreaterEqual(live["total_tickets"], 2)
        self.assertIn("category_distribution", live)
        self.assertIn("priority_distribution", live)
        # Verify offline benchmark key exists (even if None or dict)
        self.assertIn("offline_evaluation_benchmark", data)


if __name__ == "__main__":
    unittest.main()
