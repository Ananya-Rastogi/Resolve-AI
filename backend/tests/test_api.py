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

    def test_10_user_profile(self):
        """Verify GET and PATCH /api/user/profile endpoints."""
        # Test GET profile
        get_res = self.client.get("/api/user/profile", headers={"Authorization": "Bearer dev-agent-42"})
        self.assertEqual(get_res.status_code, 200)
        profile = get_res.json()
        self.assertEqual(profile["id"], "dev-agent-42")

        # Test PATCH profile (name, theme, preferences)
        patch_res = self.client.patch(
            "/api/user/profile",
            headers={"Authorization": "Bearer dev-agent-42"},
            json={
                "full_name": "Senior Agent Jane",
                "theme": "dark",
                "preferences": {"notifications": True, "simple_mode": True, "compact_view": True},
            },
        )
        self.assertEqual(patch_res.status_code, 200)
        updated = patch_res.json()
        self.assertEqual(updated["full_name"], "Senior Agent Jane")
        self.assertEqual(updated["theme"], "dark")
        self.assertTrue(updated["preferences"].get("compact_view"))

    def test_11_ticket_with_user_id(self):
        """Verify ticket creation associates user_id when authenticated."""
        payload = {
            "subject": "System cannot connect to database instance after cluster failover",
            "customer_name": "DevOps User",
            "tier": "Gold",
        }
        res = self.client.post("/api/tickets", json=payload, headers={"Authorization": "Bearer dev-agent-42"})
        self.assertEqual(res.status_code, 201)
        ticket = res.json()
        self.assertEqual(ticket["user_id"], "dev-agent-42")

        # Verify filtering by user_id
        list_res = self.client.get("/api/tickets?user_id=dev-agent-42")
        self.assertEqual(list_res.status_code, 200)
        items = list_res.json()["items"]
        self.assertTrue(any(t["ticket_id"] == ticket["ticket_id"] for t in items))

    def test_12_two_users_data_isolation_and_role_protection(self):
        """
        Verify that User A and User B have separate private ticket scopes,
        and that ordinary users cannot elevate their role to admin.
        """
        # 1. User Alpha creates ticket A
        payload_alpha = {
            "subject": "User Alpha private financial billing question",
            "customer_name": "Alpha Customer",
            "tier": "Platinum",
        }
        res_a = self.client.post("/api/tickets", json=payload_alpha, headers={"Authorization": "Bearer dev-user-alpha"})
        self.assertEqual(res_a.status_code, 201)
        ticket_a = res_a.json()
        self.assertEqual(ticket_a["user_id"], "dev-user-alpha")

        # 2. User Beta creates ticket B
        payload_beta = {
            "subject": "User Beta private server credentials inquiry",
            "customer_name": "Beta Customer",
            "tier": "Silver",
        }
        res_b = self.client.post("/api/tickets", json=payload_beta, headers={"Authorization": "Bearer dev-user-beta"})
        self.assertEqual(res_b.status_code, 201)
        ticket_b = res_b.json()
        self.assertEqual(ticket_b["user_id"], "dev-user-beta")

        # 3. User Beta lists tickets filtered for dev-user-beta: should contain Ticket B, NOT Ticket A
        list_beta = self.client.get("/api/tickets?user_id=dev-user-beta", headers={"Authorization": "Bearer dev-user-beta"})
        self.assertEqual(list_beta.status_code, 200)
        beta_ids = [t["ticket_id"] for t in list_beta.json()["items"]]
        self.assertIn(ticket_b["ticket_id"], beta_ids)
        self.assertNotIn(ticket_a["ticket_id"], beta_ids)

        # 4. User Alpha lists tickets filtered for dev-user-alpha: should contain Ticket A, NOT Ticket B
        list_alpha = self.client.get("/api/tickets?user_id=dev-user-alpha", headers={"Authorization": "Bearer dev-user-alpha"})
        self.assertEqual(list_alpha.status_code, 200)
        alpha_ids = [t["ticket_id"] for t in list_alpha.json()["items"]]
        self.assertIn(ticket_a["ticket_id"], alpha_ids)
        self.assertNotIn(ticket_b["ticket_id"], alpha_ids)

        # 5. User Beta attempts to self-promote to 'admin' via PATCH /api/user/profile
        patch_res = self.client.patch(
            "/api/user/profile",
            headers={"Authorization": "Bearer dev-user-beta"},
            json={
                "full_name": "Beta Agent",
                "role": "admin",  # Malicious attempt to self-promote
            },
        )
        self.assertEqual(patch_res.status_code, 200)
        profile_beta = patch_res.json()
        # Verify role was NOT changed to admin (stays 'agent')
        self.assertEqual(profile_beta["role"], "agent")

    def test_13_cross_agent_ticket_isolation_and_admin_management(self):
        """
        Verify:
        - Cross-agent ticket view and update return 403 Forbidden.
        - Non-admins cannot call the admin role management endpoint.
        - Admins can manage roles.
        """
        # Create ticket for User Alpha
        tkt_res = self.client.post(
            "/api/tickets",
            json={"subject": "Confidential Alpha payroll inquiry", "customer_name": "Employee A", "tier": "Gold"},
            headers={"Authorization": "Bearer dev-agent-alpha"},
        )
        self.assertEqual(tkt_res.status_code, 201)
        ticket_id = tkt_res.json()["ticket_id"]

        # User Beta attempts to view Alpha's ticket -> 403 Forbidden
        view_res = self.client.get(
            f"/api/tickets/{ticket_id}",
            headers={"Authorization": "Bearer dev-agent-beta"},
        )
        self.assertEqual(view_res.status_code, 403)

        # User Beta attempts to update Alpha's ticket -> 403 Forbidden
        upd_res = self.client.patch(
            f"/api/tickets/{ticket_id}",
            json={"status": "resolved"},
            headers={"Authorization": "Bearer dev-agent-beta"},
        )
        self.assertEqual(upd_res.status_code, 403)

        # User Beta attempts to list Alpha's private queue -> 403 Forbidden
        list_res = self.client.get(
            "/api/tickets?user_id=dev-agent-alpha",
            headers={"Authorization": "Bearer dev-agent-beta"},
        )
        self.assertEqual(list_res.status_code, 403)

        # Non-admin attempts to access admin role endpoint -> 403 Forbidden
        role_res = self.client.patch(
            "/api/admin/users/dev-agent-beta/role",
            json={"role": "admin"},
            headers={"Authorization": "Bearer dev-agent-beta"},
        )
        self.assertEqual(role_res.status_code, 403)

        # Initialize an admin user in repository
        from app.db.repository import get_repository
        repo = get_repository()
        repo.update_user_role_admin("dev-admin-supervisor", "admin")

        # Admin calls admin role management endpoint -> 200 OK
        admin_res = self.client.patch(
            "/api/admin/users/dev-agent-beta/role",
            json={"role": "manager"},
            headers={"Authorization": "Bearer dev-admin-supervisor"},
        )
        self.assertEqual(admin_res.status_code, 200)
        self.assertEqual(admin_res.json()["role"], "manager")

    def test_14_unassigned_ticket_intake_and_claiming(self):
        """
        Verify that unassigned intake tickets can be viewed by agents,
        and claiming the ticket locks it to that agent.
        """
        # Create unassigned ticket (public intake)
        res = self.client.post(
            "/api/tickets",
            json={"subject": "General unassigned support request", "customer_name": "Public Guest", "tier": "Bronze"},
        )
        self.assertEqual(res.status_code, 201)
        tkt = res.json()
        tkt_id = tkt["ticket_id"]
        self.assertIsNone(tkt["user_id"])

        # Agent Alpha views unassigned ticket -> 200 OK
        view_a = self.client.get(f"/api/tickets/{tkt_id}", headers={"Authorization": "Bearer dev-agent-alpha"})
        self.assertEqual(view_a.status_code, 200)

        # Agent Alpha claims/updates the ticket -> ticket becomes owned by Agent Alpha
        claim_res = self.client.patch(
            f"/api/tickets/{tkt_id}",
            json={"status": "in_progress"},
            headers={"Authorization": "Bearer dev-agent-alpha"},
        )
        self.assertEqual(claim_res.status_code, 200)
        self.assertEqual(claim_res.json()["user_id"], "dev-agent-alpha")

        # Agent Gamma (ordinary agent) tries to update Agent Alpha's claimed ticket -> 403 Forbidden
        gamma_upd = self.client.patch(
            f"/api/tickets/{tkt_id}",
            json={"status": "resolved"},
            headers={"Authorization": "Bearer dev-agent-gamma"},
        )
        self.assertEqual(gamma_upd.status_code, 403)

        # Manager Beta (promoted to manager in test 13) has managerial override -> 200 OK
        manager_upd = self.client.patch(
            f"/api/tickets/{tkt_id}",
            json={"status": "resolved"},
            headers={"Authorization": "Bearer dev-agent-beta"},
        )
        self.assertEqual(manager_upd.status_code, 200)

    def test_15_admin_bootstrap_and_lockout(self):
        """
        Verify the one-time administrator bootstrap procedure:
        - Rejects bootstrapping nonexistent users
        - Promotes the first administrator successfully
        - Permanently locks out subsequent bootstrap attempts once an admin exists
        """
        from app.db.repository import SQLiteRepository
        # Isolated in-memory repository with zero initial users/admins
        test_repo = SQLiteRepository(db_path=":memory:")

        # Attempt bootstrap when no profiles exist -> error
        with self.assertRaises(ValueError) as ctx:
            test_repo.bootstrap_first_admin("nobody@example.com")
        self.assertIn("does not exist", str(ctx.exception))

        # Create first user as regular agent
        test_repo.update_user_profile(
            "user-first-boot",
            {"email": "first_admin@example.com", "full_name": "First Admin Candidate"}
        )
        p1 = test_repo.get_user_profile("user-first-boot")
        self.assertEqual(p1["role"], "agent")

        # Run bootstrap for first user -> SUCCESS
        result = test_repo.bootstrap_first_admin("first_admin@example.com")
        self.assertIn("Success", result)

        p1_after = test_repo.get_user_profile("user-first-boot")
        self.assertEqual(p1_after["role"], "admin")

        # Create second user
        test_repo.update_user_profile(
            "user-second-boot",
            {"email": "second_user@example.com", "full_name": "Second User"}
        )

        # Attempt to run bootstrap AGAIN -> PERMANENTLY LOCKED
        with self.assertRaises(ValueError) as ctx2:
            test_repo.bootstrap_first_admin("second_user@example.com")
        self.assertIn("Bootstrap procedure is permanently locked", str(ctx2.exception))

        # Verify second user was NOT elevated
        p2 = test_repo.get_user_profile("user-second-boot")
        self.assertEqual(p2["role"], "agent")


if __name__ == "__main__":
    unittest.main()


