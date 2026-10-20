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
        cls.admin_headers = {"Authorization": "Bearer dev-admin-test"}
        cls.test_repo.update_user_role_admin("dev-admin-test", "admin")

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
        """Verify GET /api/tickets requires authentication, supports pagination and query filters."""
        # Unauthenticated request rejected with 401
        unauth_res = self.client.get("/api/tickets?page=1&limit=10")
        self.assertEqual(unauth_res.status_code, 401)

        # Create a second ticket with shipping
        self.client.post(
            "/api/tickets",
            json={
                "subject": "Tracking link not working for my express parcel",
                "customer_name": "Charlie",
                "tier": "Silver",
            },
        )

        response = self.client.get("/api/tickets?page=1&limit=10", headers=self.admin_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(data["total"], 2)
        self.assertGreaterEqual(len(data["items"]), 2)

        # Filter by category=billing
        billing_res = self.client.get("/api/tickets?category=billing", headers=self.admin_headers)
        self.assertEqual(billing_res.status_code, 200)
        billing_items = billing_res.json()["items"]
        self.assertTrue(all(item["category"] == "billing" for item in billing_items))

    def test_06_get_ticket_details(self):
        """Verify GET /api/tickets/{ticket_id} requires auth and returns full analysis and audit history."""
        # Fetch first ticket
        list_res = self.client.get("/api/tickets?limit=1", headers=self.admin_headers)
        ticket_id = list_res.json()["items"][0]["ticket_id"]

        # Unauthenticated request rejected
        unauth_res = self.client.get(f"/api/tickets/{ticket_id}")
        self.assertEqual(unauth_res.status_code, 401)

        detail_res = self.client.get(f"/api/tickets/{ticket_id}", headers=self.admin_headers)
        self.assertEqual(detail_res.status_code, 200)
        detail = detail_res.json()
        self.assertEqual(detail["ticket_id"], ticket_id)
        self.assertIsNotNone(detail.get("analysis"))
        self.assertIsInstance(detail.get("events"), list)

    def test_07_get_ticket_not_found(self):
        """Verify GET /api/tickets/{non_existent} returns 404 for authorized user."""
        response = self.client.get("/api/tickets/TKT-DOES-NOT-EXIST", headers=self.admin_headers)
        self.assertEqual(response.status_code, 404)

    def test_08_update_ticket(self):
        """Verify PATCH /api/tickets/{ticket_id} requires auth and safely updates status and assigned team."""
        list_res = self.client.get("/api/tickets?limit=1", headers=self.admin_headers)
        ticket_id = list_res.json()["items"][0]["ticket_id"]

        # Unauthenticated update rejected
        unauth_res = self.client.patch(
            f"/api/tickets/{ticket_id}",
            json={"status": "resolved", "assigned_team": "Billing Support", "actor": "manager_alice"},
        )
        self.assertEqual(unauth_res.status_code, 401)

        patch_res = self.client.patch(
            f"/api/tickets/{ticket_id}",
            json={"status": "resolved", "assigned_team": "Billing Support", "actor": "manager_alice"},
            headers=self.admin_headers,
        )
        self.assertEqual(patch_res.status_code, 200)
        updated = patch_res.json()
        self.assertEqual(updated["status"], "resolved")

        # Verify audit event was logged
        detail_res = self.client.get(f"/api/tickets/{ticket_id}", headers=self.admin_headers)
        events = detail_res.json().get("events", [])
        update_events = [e for e in events if e.get("event_type") == "ticket_updated"]
        self.assertGreaterEqual(len(update_events), 1)

    def test_09_analytics_endpoint(self):
        """Verify GET /api/analytics requires auth and returns real aggregated statistics."""
        # Unauthenticated request rejected
        unauth = self.client.get("/api/analytics")
        self.assertEqual(unauth.status_code, 401)

        response = self.client.get("/api/analytics", headers=self.admin_headers)
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

        # Verify filtering by user_id with authorized caller
        list_res = self.client.get("/api/tickets?user_id=dev-agent-42", headers={"Authorization": "Bearer dev-agent-42"})
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

    def test_16_security_unauthenticated_requests_rejected(self):
        """
        Verify all sensitive ticket and duplicate endpoints strictly reject unauthenticated requests with 401.
        """
        # 1. Ticket list
        res_list = self.client.get("/api/tickets")
        self.assertEqual(res_list.status_code, 401)

        # 2. Ticket details
        res_detail = self.client.get("/api/tickets/TKT-SAMPLE-001")
        self.assertEqual(res_detail.status_code, 401)

        # 3. Ticket updates
        res_patch = self.client.patch("/api/tickets/TKT-SAMPLE-001", json={"status": "resolved"})
        self.assertEqual(res_patch.status_code, 401)

        # 4. Analytics
        res_analytics = self.client.get("/api/analytics")
        self.assertEqual(res_analytics.status_code, 401)

        # 5. Duplicate check POST
        res_dup_post = self.client.post("/api/tickets/check-duplicates", json={"subject": "Payment refund inquiry"})
        self.assertEqual(res_dup_post.status_code, 401)

        # 6. Duplicate check GET
        res_dup_get = self.client.get("/api/tickets/TKT-SAMPLE-001/duplicates")
        self.assertEqual(res_dup_get.status_code, 401)

    def test_17_security_forged_unsigned_jwts_rejected(self):
        """
        Verify that forged, unsigned, or unverified JWTs are rejected and never trusted.
        """
        forged_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhdHRhY2tlci1hZG1pbiIsImVtYWlsIjoiaGFja2VyQGF0dGFjay5jb20iLCJyb2xlIjoiYWRtaW4ifQ.invalidsignature123"
        forged_headers = {"Authorization": f"Bearer {forged_jwt}"}

        res_list = self.client.get("/api/tickets", headers=forged_headers)
        self.assertEqual(res_list.status_code, 401)

        res_dup = self.client.post("/api/tickets/check-duplicates", json={"subject": "Billing issue"}, headers=forged_headers)
        self.assertEqual(res_dup.status_code, 401)

        random_headers = {"Authorization": "Bearer arbitrary-fake-token-string"}
        res_random = self.client.get("/api/tickets", headers=random_headers)
        self.assertEqual(res_random.status_code, 401)

    def test_18_security_user_id_param_spoofing_blocked(self):
        """
        Verify that supplying ?user_id=target-user cannot bypass authorization for unauthenticated users or agents.
        """
        # Unauthenticated user supplies ?user_id=dev-user-alpha -> 401
        res_unauth = self.client.get("/api/tickets?user_id=dev-user-alpha")
        self.assertEqual(res_unauth.status_code, 401)

        # Non-admin agent dev-user-beta supplies ?user_id=dev-user-alpha -> 403 Forbidden
        res_agent = self.client.get(
            "/api/tickets?user_id=dev-user-alpha",
            headers={"Authorization": "Bearer dev-user-beta"},
        )
        self.assertEqual(res_agent.status_code, 403)

    def test_19_security_duplicate_check_authorization_and_isolation(self):
        """
        Verify that duplicate detection enforces user isolation and never leaks cross-tenant ticket subjects or IDs.
        """
        # 1. User Alpha creates ticket with sensitive subject
        res_a = self.client.post(
            "/api/tickets",
            json={
                "subject": "Confidential Alpha corporate credit card compromise report",
                "customer_name": "Alpha Corp",
                "tier": "Platinum",
            },
            headers={"Authorization": "Bearer dev-user-alpha"},
        )
        self.assertEqual(res_a.status_code, 201)
        ticket_a_id = res_a.json()["ticket_id"]

        # 2. User Beta checks duplicates for the exact same subject -> should find 0 matches
        res_beta_dup = self.client.post(
            "/api/tickets/check-duplicates",
            json={"subject": "Confidential Alpha corporate credit card compromise report"},
            headers={"Authorization": "Bearer dev-user-beta"},
        )
        self.assertEqual(res_beta_dup.status_code, 200)
        beta_matches = res_beta_dup.json()["matches"]
        matched_ids = [m["ticket_id"] for m in beta_matches]
        self.assertNotIn(ticket_a_id, matched_ids)
        self.assertEqual(len(beta_matches), 0)

        # 3. User Alpha checks duplicates -> finds Ticket A
        res_alpha_dup = self.client.post(
            "/api/tickets/check-duplicates",
            json={"subject": "Confidential Alpha corporate credit card compromise report"},
            headers={"Authorization": "Bearer dev-user-alpha"},
        )
        self.assertEqual(res_alpha_dup.status_code, 200)
        alpha_matches = res_alpha_dup.json()["matches"]
        alpha_matched_ids = [m["ticket_id"] for m in alpha_matches]
        self.assertIn(ticket_a_id, alpha_matched_ids)

        # 4. User Beta attempts to query ticket duplicates endpoint for Ticket A -> 403 Forbidden
        res_beta_direct = self.client.get(
            f"/api/tickets/{ticket_a_id}/duplicates",
            headers={"Authorization": "Bearer dev-user-beta"},
        )
        self.assertEqual(res_beta_direct.status_code, 403)

        # 5. User Alpha queries ticket duplicates endpoint for Ticket A -> 200 OK
        res_alpha_direct = self.client.get(
            f"/api/tickets/{ticket_a_id}/duplicates",
            headers={"Authorization": "Bearer dev-user-alpha"},
        )
        self.assertEqual(res_alpha_direct.status_code, 200)

    def test_18_supabase_token_verification_and_unauthorized_regression(self):
        """
        Regression test for Issue 1:
        1. An unverified/invalid Bearer token returns 401 Unauthorized when requesting ticket details.
        2. A verified Supabase auth token authenticates the user, allowing access to their own ticket.
        3. Ticket creation, listing, and detail retrieval use consistent authenticated identity.
        4. Cross-user ticket access remains forbidden (403).
        """
        from unittest.mock import MagicMock, patch

        # 1. Unverified token returns 401 Unauthorized
        tkt_res = self.client.post(
            "/api/tickets",
            json={"subject": "Regression test ticket for auth verification", "customer_name": "Test User", "tier": "Gold"},
            headers={"Authorization": "Bearer dev-agent-regression"},
        )
        self.assertEqual(tkt_res.status_code, 201)
        ticket_id = tkt_res.json()["ticket_id"]

        invalid_res = self.client.get(
            f"/api/tickets/{ticket_id}",
            headers={"Authorization": "Bearer invalid.fake.token"},
        )
        self.assertEqual(invalid_res.status_code, 401)
        self.assertIn("Authentication required", invalid_res.json()["detail"])

        # 2. Mock Supabase Auth verification to simulate valid Supabase token
        mock_user = MagicMock()
        mock_user.id = "supabase-user-uuid-1234"
        mock_user.email = "specialist@enterprise.io"
        mock_user.user_metadata = {"full_name": "Enterprise Specialist"}

        mock_auth_res = MagicMock()
        mock_auth_res.user = mock_user

        mock_supabase_client = MagicMock()
        mock_supabase_client.auth.get_user.return_value = mock_auth_res

        with patch("app.api.main.get_supabase_auth_client", return_value=mock_supabase_client):
            # 3. Create ticket with Supabase JWT
            jwt_token = "valid.supabase.jwt"
            create_res = self.client.post(
                "/api/tickets",
                json={"subject": "Supabase authenticated user ticket", "customer_name": "Auth Customer", "tier": "Platinum"},
                headers={"Authorization": f"Bearer {jwt_token}"},
            )
            self.assertEqual(create_res.status_code, 201)
            created_ticket = create_res.json()
            # Verified user_id bound consistently
            self.assertEqual(created_ticket["user_id"], "supabase-user-uuid-1234")
            created_id = created_ticket["ticket_id"]

            # 4. Creator retrieves full ticket detail successfully (200 OK)
            detail_res = self.client.get(
                f"/api/tickets/{created_id}",
                headers={"Authorization": f"Bearer {jwt_token}"},
            )
            self.assertEqual(detail_res.status_code, 200)
            self.assertEqual(detail_res.json()["ticket_id"], created_id)

            # 5. Different unprivileged agent attempting to view this ticket receives 403 Forbidden
            other_user_res = self.client.get(
                f"/api/tickets/{created_id}",
                headers={"Authorization": "Bearer dev-other-agent"},
            )
            self.assertEqual(other_user_res.status_code, 403)

    def test_21_process_ticket_with_uuid_event_regression(self):
        """
        Regression test for production HTTP 500 ValidationError:
        When backend constructs TicketEventSchema(**e) where e['id'] is a UUID string
        (such as returned by Supabase '87824b75-367b-49fd-bb8c-b36189e8df6b'),
        POST /api/tickets must succeed with 201 Created and return the UUID event ID intact.
        """
        original_get_events = self.test_repo.get_ticket_events
        uuid_str = "87824b75-367b-49fd-bb8c-b36189e8df6b"

        def mock_get_events(ticket_id):
            real_events = original_get_events(ticket_id)
            if real_events:
                for ev in real_events:
                    ev["id"] = uuid_str
                return real_events
            return [{
                "id": uuid_str,
                "ticket_id": ticket_id,
                "event_type": "ticket_created",
                "actor": "system",
                "details": {"action": "ticket_created"},
                "created_at": "2026-10-20T16:23:39.449612+00:00",
            }]

        self.test_repo.get_ticket_events = mock_get_events
        try:
            payload = {
                "subject": "Urgent UUID event test for Supabase production bug regression",
                "customer_name": "UUID Tester",
                "customer_id": "CUST-UUID-1",
                "email": "uuid@example.com",
                "tier": "Gold",
            }
            res = self.client.post("/api/tickets", json=payload)
            self.assertEqual(res.status_code, 201, f"Expected 201 but got {res.status_code}: {res.text}")
            data = res.json()
            self.assertIn("events", data)
            self.assertGreaterEqual(len(data["events"]), 1)
            event_ids = [ev["id"] for ev in data["events"]]
            self.assertIn(uuid_str, event_ids)

            # Also verify GET /api/tickets/{ticket_id} detail returns 200 with UUID event
            ticket_id = data["ticket_id"]
            get_res = self.client.get(f"/api/tickets/{ticket_id}", headers=self.admin_headers)
            self.assertEqual(get_res.status_code, 200)
            get_data = get_res.json()
            get_event_ids = [ev["id"] for ev in get_data["events"]]
            self.assertIn(uuid_str, get_event_ids)
        finally:
            self.test_repo.get_ticket_events = original_get_events


if __name__ == "__main__":
    unittest.main()


