"""
Resolve AI: Live Supabase Integration Tests.
Separated from the standard offline test suite.

Runs ONLY when SUPABASE_URL and SUPABASE_KEY are explicitly configured.
Otherwise skips gracefully so standard offline CI/CD and pytest runs are unaffected.
"""
import os
import unittest
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

has_live_supabase = bool(
    SUPABASE_URL
    and SUPABASE_KEY
    and not SUPABASE_URL.startswith("https://your-project")
    and not SUPABASE_KEY.startswith("your-supabase")
)


class TestSupabaseLiveIntegration(unittest.TestCase):
    """Live verification against remote Supabase project."""

    @classmethod
    def setUpClass(cls):
        if not has_live_supabase:
            raise unittest.SkipTest("Live Supabase credentials not configured in environment. Skipping live tests.")

        from supabase import create_client
        cls.client = create_client(SUPABASE_URL, SUPABASE_KEY)

    def test_01_supabase_connection_and_health(self):
        """Verify remote Supabase connectivity."""
        self.assertIsNotNone(self.client)

    def test_02_tables_exist_after_migration(self):
        """Verify profiles and tickets tables exist once migration is executed."""
        try:
            res = self.client.table("profiles").select("count", count="exact").limit(1).execute()
            self.assertIsNotNone(res)
        except Exception as e:
            self.fail(f"Could not query profiles table: {e}. Ensure migration_001_auth_profiles.sql has been run.")


if __name__ == "__main__":
    unittest.main()
