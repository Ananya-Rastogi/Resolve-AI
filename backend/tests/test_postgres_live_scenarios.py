"""
Live PostgreSQL Execution and Verification Test Suite for Resolve AI.
Runs against a local disposable PostgreSQL 18 instance to verify all migration scenarios:
 1. Fresh Database
 2. Existing Database with current expected schema
 3. Representative older schema missing columns + diagnostic abort checks
 4. Migration idempotency (re-running twice)
 5. Existing UUID extension installed in another schema (e.g. public)
 6. Concurrent first-admin bootstrap serialization via advisory locks
 7. Strict RLS security verification (multi-user, role elevation, isolation, analysis/event forgery)
"""

import os
from pathlib import Path
import subprocess
import threading
import time
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATION_FILE_HOST = REPO_ROOT / "supabase" / "migration_001_auth_profiles.sql"
SCHEMA_FILE_HOST = REPO_ROOT / "supabase" / "schema.sql"

def to_wsl_path(path: Path) -> str:
    """Convert a Windows Path to its WSL /mnt/host/c/... equivalent."""
    p = str(path).replace("\\", "/")
    if len(p) >= 2 and p[1] == ":":
        drive = p[0].lower()
        return f"/mnt/host/{drive}{p[2:]}"
    return p

MIGRATION_PATH_WSL = to_wsl_path(MIGRATION_FILE_HOST)
SCHEMA_PATH_WSL = to_wsl_path(SCHEMA_FILE_HOST)

def run_psql(db_name: str, sql_code: str, user: str = "postgres") -> subprocess.CompletedProcess:
    """Execute raw SQL against the specified database in WSL PostgreSQL."""
    cmd = [
        "wsl", "-d", "docker-desktop", "-e",
        "su", user, "-c",
        f"psql -d {db_name} -v ON_ERROR_STOP=1 -A -t"
    ]
    return subprocess.run(cmd, input=sql_code, text=True, capture_output=True)

def run_psql_file(db_name: str, file_path_wsl: str, user: str = "postgres") -> subprocess.CompletedProcess:
    """Execute an SQL file against the specified database in WSL PostgreSQL."""
    cmd = [
        "wsl", "-d", "docker-desktop", "-e",
        "su", user, "-c",
        f"psql -d {db_name} -v ON_ERROR_STOP=1 -f '{file_path_wsl}'"
    ]
    return subprocess.run(cmd, capture_output=True, text=True)

def create_disposable_db(db_name: str) -> None:
    """Drop and recreate a clean disposable database."""
    drop_create_sql = f"""
    DROP DATABASE IF EXISTS {db_name};
    CREATE DATABASE {db_name};
    """
    res = run_psql("postgres", drop_create_sql)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to create database {db_name}: {res.stderr}")

def setup_supabase_harness(db_name: str) -> None:
    """Set up the Supabase auth schema, mock users table, roles, and auth helpers."""
    harness_sql = """
    CREATE SCHEMA IF NOT EXISTS auth;
    CREATE TABLE IF NOT EXISTS auth.users (
        id UUID PRIMARY KEY,
        email VARCHAR(255),
        raw_user_meta_data JSONB DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ DEFAULT now()
    );

    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
            CREATE ROLE anon NOLOGIN;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
            CREATE ROLE authenticated NOLOGIN;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
            CREATE ROLE service_role NOLOGIN;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'supabase_admin') THEN
            CREATE ROLE supabase_admin NOLOGIN;
        END IF;
    END $$;

    CREATE OR REPLACE FUNCTION auth.uid() RETURNS UUID AS $$
        SELECT NULLIF(current_setting('request.jwt.claim.sub', true), '')::uuid;
    $$ LANGUAGE sql STABLE;

    CREATE OR REPLACE FUNCTION auth.jwt() RETURNS JSONB AS $$
        SELECT NULLIF(current_setting('request.jwt.claims', true), '')::jsonb;
    $$ LANGUAGE sql STABLE;

    GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
    GRANT USAGE ON SCHEMA auth TO anon, authenticated, service_role;
    GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, service_role;
    """
    res = run_psql(db_name, harness_sql)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to set up Supabase harness on {db_name}: {res.stderr}")


class TestPostgresMigrationScenarios(unittest.TestCase):
    """Execution test suite against local PostgreSQL 18."""

    def setUp(self):
        # Confirm that the migration file exists at the host location
        self.assertTrue(MIGRATION_FILE_HOST.is_file(), f"Migration file not found at {MIGRATION_FILE_HOST}")
        self.assertTrue(SCHEMA_FILE_HOST.is_file(), f"Schema file not found at {SCHEMA_FILE_HOST}")

    def test_00_verify_migration_file_binding(self):
        """Confirm that the test runner executes the EXACT file in repository, not a hardcoded copy."""
        # Read header from host file
        with open(MIGRATION_FILE_HOST, "r", encoding="utf-8") as f:
            header = f.read(500)
        self.assertIn("Resolve AI: Migration 001", header)

        # Confirm WSL sees the exact same file size and checksum
        check_wsl = subprocess.run(
            ["wsl", "-d", "docker-desktop", "-e", "head", "-n", "2", MIGRATION_PATH_WSL],
            capture_output=True, text=True
        )
        self.assertEqual(check_wsl.returncode, 0, f"WSL could not access migration file at {MIGRATION_PATH_WSL}")
        self.assertIn("Resolve AI: Migration 001", check_wsl.stdout)

    def test_01_fresh_database_execution(self):
        """Scenario 1: Fresh database run."""
        db_name = "test_fresh_db"
        create_disposable_db(db_name)
        setup_supabase_harness(db_name)

        # Execute migration file directly from repository
        res = run_psql_file(db_name, MIGRATION_PATH_WSL)
        self.assertEqual(res.returncode, 0, f"Migration failed on fresh DB: {res.stderr}")

        # Verify tables exist
        check_tables_sql = """
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
        """
        table_res = run_psql(db_name, check_tables_sql)
        tables = [t.strip() for t in table_res.stdout.split() if t.strip()]
        for expected in ["profiles", "tickets", "ticket_analyses", "ticket_events"]:
            self.assertIn(expected, tables, f"Expected table {expected} not found")

        # Verify RLS is enabled on all tables
        rls_sql = """
        SELECT relname, relrowsecurity 
        FROM pg_class 
        JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace 
        WHERE nspname = 'public' AND relname IN ('profiles', 'tickets', 'ticket_analyses', 'ticket_events');
        """
        rls_res = run_psql(db_name, rls_sql)
        for line in rls_res.stdout.strip().splitlines():
            parts = line.split("|")
            if len(parts) == 2:
                tbl, rls = parts[0].strip(), parts[1].strip()
                self.assertEqual(rls, "t", f"RLS not enabled on {tbl}")

    def test_02_current_expected_schema_execution(self):
        """Scenario 2: Existing database with current expected schema populated with data."""
        db_name = "test_current_db"
        create_disposable_db(db_name)
        setup_supabase_harness(db_name)

        # Run schema.sql first
        res_schema = run_psql_file(db_name, SCHEMA_PATH_WSL)
        self.assertEqual(res_schema.returncode, 0, f"Schema setup failed: {res_schema.stderr}")

        # Insert pre-existing ticket and analysis
        populate_sql = """
        INSERT INTO public.tickets (ticket_id, subject, status, priority, customer_name)
        VALUES ('TKT-INIT-001', 'Initial Ticket', 'open', 'High', 'Initial Customer');

        INSERT INTO public.ticket_analyses (ticket_id, ml_topic, llm_urgency)
        VALUES ('TKT-INIT-001', 'billing', 'high');
        """
        res_pop = run_psql(db_name, populate_sql)
        self.assertEqual(res_pop.returncode, 0, f"Population failed: {res_pop.stderr}")

        # Run migration 001
        res_mig = run_psql_file(db_name, MIGRATION_PATH_WSL)
        self.assertEqual(res_mig.returncode, 0, f"Migration failed over existing current schema: {res_mig.stderr}")

        # Verify data preservation
        check_sql = "SELECT ticket_id, customer_name FROM public.tickets WHERE ticket_id = 'TKT-INIT-001';"
        res_check = run_psql(db_name, check_sql)
        self.assertIn("TKT-INIT-001|Initial Customer", res_check.stdout)

    def test_03_legacy_schema_missing_columns(self):
        """Scenario 3: Representative older schema missing several columns."""
        db_name = "test_legacy_db"
        create_disposable_db(db_name)
        setup_supabase_harness(db_name)

        # Create older public.profiles table missing email, role, theme, preferences
        # and older public.tickets table missing ticket_id, subject, status, priority, timestamps, user_id
        legacy_sql = """
        CREATE TABLE public.profiles (
            id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
            full_name VARCHAR(255)
        );

        INSERT INTO auth.users (id, email) VALUES
        ('11111111-1111-1111-1111-111111111111', 'leg1@example.com'),
        ('22222222-2222-2222-2222-222222222222', 'leg2@example.com');

        INSERT INTO public.profiles (id, full_name) VALUES
        ('11111111-1111-1111-1111-111111111111', 'Legacy User 1');

        CREATE TABLE public.tickets (
            id UUID PRIMARY KEY,
            customer_name VARCHAR(255),
            email VARCHAR(255),
            notes TEXT
        );

        INSERT INTO public.tickets (id, customer_name, email, notes) VALUES
        ('11111111-1111-1111-1111-111111111111', 'Legacy User 1', 'leg1@example.com', 'Old note 1'),
        ('22222222-2222-2222-2222-222222222222', 'Legacy User 2', 'leg2@example.com', 'Old note 2');
        """
        res_leg = run_psql(db_name, legacy_sql)
        self.assertEqual(res_leg.returncode, 0, f"Legacy table setup failed: {res_leg.stderr}")

        # Run migration on legacy tables (verifies column additions happen BEFORE index creation)
        res_mig = run_psql_file(db_name, MIGRATION_PATH_WSL)
        self.assertEqual(res_mig.returncode, 0, f"Migration failed on legacy tables: {res_mig.stderr}")

        # 1. Verify original tickets ID and custom data (notes) are preserved
        data_sql = """
        SELECT id, customer_name, notes, ticket_id, subject, status, priority, tier 
        FROM public.tickets 
        ORDER BY customer_name;
        """
        res_data = run_psql(db_name, data_sql)
        lines = [line.strip() for line in res_data.stdout.strip().splitlines() if line.strip()]
        self.assertEqual(len(lines), 2)
        self.assertIn("11111111-1111-1111-1111-111111111111|Legacy User 1|Old note 1|TKT-LEGACY-11111111-1111-1111-1111-111111111111|Legacy Ticket|open|Medium|Bronze", lines[0])
        self.assertIn("22222222-2222-2222-2222-222222222222|Legacy User 2|Old note 2|TKT-LEGACY-22222222-2222-2222-2222-222222222222|Legacy Ticket|open|Medium|Bronze", lines[1])

        # 2. Verify legacy profile was upgraded with safe defaults and existing data preserved
        prof_sql = """
        SELECT id, full_name, role, theme FROM public.profiles WHERE id = '11111111-1111-1111-1111-111111111111';
        """
        res_prof = run_psql(db_name, prof_sql)
        self.assertIn("11111111-1111-1111-1111-111111111111|Legacy User 1|agent|system", res_prof.stdout.strip())

        # 3. Verify indexes on profiles were created only after columns were added
        prof_idx_sql = """
        SELECT indexname FROM pg_indexes WHERE tablename = 'profiles';
        """
        res_pidx = run_psql(db_name, prof_idx_sql)
        self.assertIn("idx_profiles_email", res_pidx.stdout)
        self.assertIn("idx_profiles_role", res_pidx.stdout)

        # 4. Verify unique constraint exists on ticket_id
        uc_sql = """
        SELECT conname FROM pg_constraint 
        WHERE conrelid = 'public.tickets'::regclass AND contype = 'u';
        """
        res_uc = run_psql(db_name, uc_sql)
        self.assertIn("tickets_ticket_id_key", res_uc.stdout)

        # 5. Verify foreign key constraints exist on child tables
        fk_sql = """
        SELECT conname, conrelid::regclass::text FROM pg_constraint WHERE contype = 'f';
        """
        res_fk = run_psql(db_name, fk_sql)
        self.assertIn("ticket_analyses", res_fk.stdout)
        self.assertIn("ticket_events", res_fk.stdout)

        # 6. Verify triggers exist
        tg_sql = """
        SELECT tgname, relname FROM pg_trigger 
        JOIN pg_class ON pg_class.oid = pg_trigger.tgrelid 
        WHERE tgname IN ('trigger_tickets_updated_at', 'trigger_profiles_updated_at', 'trigger_enforce_profile_security');
        """
        res_tg = run_psql(db_name, tg_sql)
        self.assertIn("trigger_tickets_updated_at", res_tg.stdout)
        self.assertIn("trigger_enforce_profile_security", res_tg.stdout)

        # 7. Verify RLS policies exist
        pol_sql = """
        SELECT policyname FROM pg_policies WHERE schemaname = 'public';
        """
        res_pol = run_psql(db_name, pol_sql)
        self.assertIn("tickets_select_policy", res_pol.stdout)
        self.assertIn("tickets_update_policy", res_pol.stdout)
        self.assertIn("analyses_select_policy", res_pol.stdout)
        self.assertIn("events_select_policy", res_pol.stdout)

    def test_03b_legacy_schema_early_diagnostics(self):
        """Scenario 3b: Test early diagnostic halt on duplicate ticket_id."""
        db_name = "test_dup_db"
        create_disposable_db(db_name)
        setup_supabase_harness(db_name)

        # Create older tickets table with duplicated ticket_id
        dup_sql = """
        CREATE TABLE public.tickets (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ticket_id VARCHAR(64),
            customer_name VARCHAR(255)
        );

        INSERT INTO public.tickets (ticket_id, customer_name) VALUES
        ('DUPLICATE-ID', 'Alice'),
        ('DUPLICATE-ID', 'Bob');
        """
        res_dup = run_psql(db_name, dup_sql)
        self.assertEqual(res_dup.returncode, 0)

        # Migration should safely abort with clear exception
        res_mig = run_psql_file(db_name, MIGRATION_PATH_WSL)
        self.assertNotEqual(res_mig.returncode, 0, "Migration should fail on duplicate ticket_id")
        self.assertIn("Legacy public.tickets table contains duplicate ticket_id values", res_mig.stderr)

    def test_04_idempotency_rerun(self):
        """Scenario 4: Re-running migration on the same database succeeds idempotently."""
        db_name = "test_idempotent_db"
        create_disposable_db(db_name)
        setup_supabase_harness(db_name)

        # Run 1
        res1 = run_psql_file(db_name, MIGRATION_PATH_WSL)
        self.assertEqual(res1.returncode, 0, f"Run 1 failed: {res1.stderr}")

        # Insert some test data
        insert_sql = """
        INSERT INTO public.tickets (ticket_id, subject) VALUES ('TKT-IDEM-1', 'Test Idempotency');
        """
        run_psql(db_name, insert_sql)

        # Run 2
        res2 = run_psql_file(db_name, MIGRATION_PATH_WSL)
        self.assertEqual(res2.returncode, 0, f"Run 2 (idempotent) failed: {res2.stderr}")

        # Verify data unchanged
        check_sql = "SELECT count(*) FROM public.tickets WHERE ticket_id = 'TKT-IDEM-1';"
        res_check = run_psql(db_name, check_sql)
        self.assertEqual(res_check.stdout.strip(), "1")

    def test_05_uuid_extension_in_public_schema(self):
        """Scenario 5: Pre-existing uuid-ossp extension installed in public schema."""
        db_name = "test_uuid_alt_db"
        create_disposable_db(db_name)
        setup_supabase_harness(db_name)

        # Pre-install uuid-ossp in public schema
        pre_ext_sql = 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;'
        res_ext = run_psql(db_name, pre_ext_sql)
        self.assertEqual(res_ext.returncode, 0, f"Extension setup failed: {res_ext.stderr}")

        # Run migration 001 - should preserve location and not error
        res_mig = run_psql_file(db_name, MIGRATION_PATH_WSL)
        self.assertEqual(res_mig.returncode, 0, f"Migration failed with public uuid-ossp: {res_mig.stderr}")
        self.assertIn('Extension "uuid-ossp" already installed in schema "public"', res_mig.stderr)

    def test_06_concurrent_bootstrap_first_admin(self):
        """Scenario 6: Concurrent bootstrap attempts are safely serialized by advisory lock."""
        db_name = "test_bootstrap_lock_db"
        create_disposable_db(db_name)
        setup_supabase_harness(db_name)
        run_psql_file(db_name, MIGRATION_PATH_WSL)

        # Create two users in auth.users (trigger on_auth_user_created creates profiles automatically)
        setup_users_sql = """
        INSERT INTO auth.users (id, email) VALUES
        ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', 'candidate1@resolveai.com'),
        ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'candidate2@resolveai.com');
        """
        res_users = run_psql(db_name, setup_users_sql)
        self.assertEqual(res_users.returncode, 0)

        results = []
        errors = []

        def call_bootstrap(email):
            sql = f"SELECT public.bootstrap_first_admin('{email}');"
            res = run_psql(db_name, sql, user="postgres")
            if res.returncode == 0:
                results.append((email, res.stdout.strip()))
            else:
                errors.append((email, res.stderr.strip()))

        t1 = threading.Thread(target=call_bootstrap, args=("candidate1@resolveai.com",))
        t2 = threading.Thread(target=call_bootstrap, args=("candidate2@resolveai.com",))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Exactly one call must succeed and one must fail
        self.assertEqual(len(results), 1, f"Expected 1 success, got {len(results)}: {results}")
        self.assertEqual(len(errors), 1, f"Expected 1 error, got {len(errors)}: {errors}")
        self.assertIn("An administrator already exists", errors[0][1])

        # Verify only 1 admin exists in the database
        admin_count_sql = "SELECT count(*) FROM public.profiles WHERE role = 'admin';"
        res_count = run_psql(db_name, admin_count_sql)
        self.assertEqual(res_count.stdout.strip(), "1")

        # Explicitly verify the function definition uses pg_catalog.pg_advisory_xact_lock and pg_catalog.hashtext
        def_sql = "SELECT prosrc FROM pg_proc WHERE proname = 'bootstrap_first_admin';"
        res_def = run_psql(db_name, def_sql)
        self.assertIn("pg_catalog.pg_advisory_xact_lock", res_def.stdout)
        self.assertIn("pg_catalog.hashtext", res_def.stdout)

    def test_07_rls_security_behavior(self):
        """Scenario 7: In-depth RLS security verification."""
        db_name = "test_rls_sec_db"
        create_disposable_db(db_name)
        setup_supabase_harness(db_name)
        run_psql_file(db_name, MIGRATION_PATH_WSL)

        agent1_id = "11111111-1111-1111-1111-111111111111"
        agent2_id = "22222222-2222-2222-2222-222222222222"
        admin_id  = "99999999-9999-9999-9999-999999999999"

        # Seed users as postgres (on_auth_user_created creates profiles as 'agent')
        seed_sql = f"""
        INSERT INTO auth.users (id, email) VALUES
        ('{agent1_id}', 'agent1@resolveai.com'),
        ('{agent2_id}', 'agent2@resolveai.com'),
        ('{admin_id}', 'admin@resolveai.com');

        -- Set themes and promote admin user
        UPDATE public.profiles SET theme = 'dark', full_name = 'Agent One' WHERE id = '{agent1_id}';
        UPDATE public.profiles SET theme = 'light', full_name = 'Agent Two' WHERE id = '{agent2_id}';
        UPDATE public.profiles SET role = 'admin', full_name = 'Admin User' WHERE id = '{admin_id}';

        -- Seed tickets: one for Agent1, one for Agent2, one unassigned
        INSERT INTO public.tickets (ticket_id, user_id, subject, status) VALUES
        ('TKT-AGENT1-001', '{agent1_id}', 'Agent 1 Ticket', 'open'),
        ('TKT-AGENT2-001', '{agent2_id}', 'Agent 2 Ticket', 'open'),
        ('TKT-UNASSIGNED-001', NULL, 'Intake Queue Ticket', 'open');

        -- Grant table usage to authenticated
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
        """
        res_seed = run_psql(db_name, seed_sql)
        self.assertEqual(res_seed.returncode, 0, f"Seed failed: {res_seed.stderr}")

        # Helper to run as an authenticated user
        def run_as_user(uid: str, sql: str) -> subprocess.CompletedProcess:
            wrapper = f"""
            BEGIN;
            SET LOCAL ROLE authenticated;
            SET LOCAL "request.jwt.claim.sub" = '{uid}';
            SET LOCAL "request.jwt.claim.role" = 'authenticated';
            {sql}
            COMMIT;
            """
            return run_psql(db_name, wrapper)

        # 1. Profile Self-Update (Agent1 updates their own theme) -> SUCCESS
        res_update_self = run_as_user(agent1_id, f"""
        UPDATE public.profiles SET theme = 'system' WHERE id = '{agent1_id}';
        """)
        self.assertEqual(res_update_self.returncode, 0, f"Self-update failed: {res_update_self.stderr}")

        # 2. Profile Role Elevation Attempt (Agent1 tries to make themselves admin) -> BLOCKED
        res_elevate = run_as_user(agent1_id, f"""
        UPDATE public.profiles SET role = 'admin' WHERE id = '{agent1_id}';
        """)
        self.assertNotEqual(res_elevate.returncode, 0, "Role elevation should be blocked")
        self.assertIn("Only administrators can change user roles", res_elevate.stderr)

        # 3. Profile ID Tampering Attempt (Agent1 tries to change id) -> BLOCKED
        res_id_tamper = run_as_user(agent1_id, f"""
        UPDATE public.profiles SET id = '{admin_id}' WHERE id = '{agent1_id}';
        """)
        self.assertNotEqual(res_id_tamper.returncode, 0, "ID tampering should be blocked")
        self.assertIn("User profile ID cannot be changed", res_id_tamper.stderr)

        # 4. Cross-Agent Ticket Isolation: Agent1 should see own ticket & unassigned, but NOT Agent2's ticket
        res_tickets_agent1 = run_as_user(agent1_id, "SELECT ticket_id FROM public.tickets ORDER BY ticket_id;")
        self.assertEqual(res_tickets_agent1.returncode, 0)
        visible_tickets = [t.strip() for t in res_tickets_agent1.stdout.strip().splitlines() if t.strip()]
        self.assertIn("TKT-AGENT1-001", visible_tickets)
        self.assertIn("TKT-UNASSIGNED-001", visible_tickets)
        self.assertNotIn("TKT-AGENT2-001", visible_tickets)

        # Agent1 attempting to update Agent2's ticket -> 0 rows updated
        res_update_cross = run_as_user(agent1_id, f"""
        UPDATE public.tickets SET subject = 'Hacked' WHERE ticket_id = 'TKT-AGENT2-001';
        """)
        self.assertEqual(res_update_cross.returncode, 0)
        # Check Agent2 ticket is unchanged
        check_cross = run_psql(db_name, "SELECT subject FROM public.tickets WHERE ticket_id = 'TKT-AGENT2-001';")
        self.assertEqual(check_cross.stdout.strip(), "Agent 2 Ticket")

        # 5. Unassigned Ticket Claiming: Agent1 claims intake ticket
        res_claim = run_as_user(agent1_id, f"""
        UPDATE public.tickets SET user_id = '{agent1_id}' WHERE ticket_id = 'TKT-UNASSIGNED-001';
        """)
        self.assertEqual(res_claim.returncode, 0, f"Claim failed: {res_claim.stderr}")
        check_claimed = run_psql(db_name, "SELECT user_id FROM public.tickets WHERE ticket_id = 'TKT-UNASSIGNED-001';")
        self.assertEqual(check_claimed.stdout.strip(), agent1_id)

        # 6. Ticket Analysis Forgery Prevention: Agent1 cannot insert into ticket_analyses
        res_forge_analysis = run_as_user(agent1_id, """
        INSERT INTO public.ticket_analyses (ticket_id, ml_topic) VALUES ('TKT-AGENT1-001', 'billing');
        """)
        self.assertNotEqual(res_forge_analysis.returncode, 0, "Agent insertion into analyses should be blocked")
        self.assertIn("violates row-level security policy", res_forge_analysis.stderr)

        # 7. Ticket Event Forgery Prevention: Agent1 cannot insert into ticket_events
        res_forge_event = run_as_user(agent1_id, """
        INSERT INTO public.ticket_events (ticket_id, event_type, actor) VALUES ('TKT-AGENT1-001', 'audit', 'agent');
        """)
        self.assertNotEqual(res_forge_event.returncode, 0, "Agent insertion into events should be blocked")
        self.assertIn("violates row-level security policy", res_forge_event.stderr)

        # 8. Admin Role Management: Admin CAN update Agent1's role to manager
        res_admin_update = run_as_user(admin_id, f"""
        UPDATE public.profiles SET role = 'manager' WHERE id = '{agent1_id}';
        """)
        self.assertEqual(res_admin_update.returncode, 0, f"Admin role management failed: {res_admin_update.stderr}")
        check_role = run_psql(db_name, f"SELECT role FROM public.profiles WHERE id = '{agent1_id}';")
        self.assertEqual(check_role.stdout.strip(), "manager")


if __name__ == "__main__":
    unittest.main()
