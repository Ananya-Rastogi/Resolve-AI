"""
Database repository supporting Supabase PostgreSQL with seamless SQLite local fallback.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

# Ensure environment variables are loaded from backend/.env or root .env
_base_dir = Path(__file__).resolve().parent.parent.parent
_env_file = _base_dir / ".env"
if _env_file.is_file():
    load_dotenv(_env_file)
else:
    load_dotenv()

logger = logging.getLogger("ticket_db")

ALLOWED_STATUSES = {"open", "in_progress", "resolved", "escalated"}
ALLOWED_PRIORITIES = {"High", "Medium", "Low"}
ALLOWED_CATEGORIES = {"billing", "shipping", "technical", "other"}
ALLOWED_TEAMS = {
    "Finance Team",
    "Logistics Team",
    "Tech Support",
    "General Support",
    "Billing Support",
    "Shipping Support",
    "Technical Support",
}
ALLOWED_TIERS = {"Platinum", "Gold", "Silver", "Bronze"}


class BaseRepository(ABC):
    """Abstract interface for ticket persistence."""

    backend_name: str = "base"

    @abstractmethod
    def save_ticket(
        self,
        ticket_data: Dict[str, Any],
        analysis_data: Optional[Dict[str, Any]] = None,
        event_details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Save a new ticket and associated analysis."""
        pass

    @abstractmethod
    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Fetch ticket by ticket_id."""
        pass

    @abstractmethod
    def list_tickets(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_team: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        user_id: Optional[str] = None,
        exclude_benchmarks: bool = True,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List tickets with filtering, search, pagination, and benchmark exclusion."""
        pass

    @abstractmethod
    def update_ticket(
        self,
        ticket_id: str,
        updates: Dict[str, Any],
        actor: str = "agent",
    ) -> Optional[Dict[str, Any]]:
        """Safely update ticket status or assignment and record an audit event."""
        pass

    @abstractmethod
    def get_ticket_analysis(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve analysis record for ticket."""
        pass

    @abstractmethod
    def get_ticket_events(self, ticket_id: str) -> List[Dict[str, Any]]:
        """Retrieve audit history events for ticket."""
        pass

    @abstractmethod
    def get_analytics(
        self,
        user_id: Optional[str] = None,
        exclude_benchmarks: bool = True,
    ) -> Dict[str, Any]:
        """Compute aggregated ticket counts and distributions with user scoping."""
        pass

    @abstractmethod
    def check_health(self) -> Dict[str, Any]:
        """Check database connectivity."""
        pass

    @abstractmethod
    def find_by_idempotency_key(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """Check for existing ticket with idempotency key."""
        pass

    @abstractmethod
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch user profile and preferences by user_id."""
        pass

    @abstractmethod
    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user profile or preferences."""
        pass

    @abstractmethod
    def update_user_role_admin(self, target_user_id: str, new_role: str) -> Optional[Dict[str, Any]]:
        """Update user role (restricted to administrators)."""
        pass

    @abstractmethod
    def bootstrap_first_admin(self, admin_email: str) -> str:
        """One-time bootstrap procedure for the first administrator."""
        pass


class SQLiteRepository(BaseRepository):
    """Local SQLite implementation for offline and development environments."""

    backend_name: str = "local_sqlite"

    def __init__(self, db_path: str = "data/tickets_dev.db"):
        self.db_path = db_path
        self._shared_conn = None
        if db_path == ":memory:":
            self._shared_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._shared_conn.row_factory = sqlite3.Row
            self._shared_conn.execute("PRAGMA foreign_keys = ON;")
        else:
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._shared_conn is not None:
            return self._shared_conn
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT UNIQUE NOT NULL,
                    user_id TEXT,
                    customer_name TEXT,
                    customer_id TEXT,
                    email TEXT,
                    tier TEXT NOT NULL DEFAULT 'Bronze',
                    subject TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open',
                    priority TEXT NOT NULL DEFAULT 'Medium',
                    category TEXT,
                    sentiment TEXT,
                    confidence REAL,
                    assigned_team TEXT,
                    escalation_level TEXT NOT NULL DEFAULT 'Not Escalated',
                    classification_source TEXT,
                    generated_reply TEXT,
                    idempotency_key TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS profiles (
                    id TEXT PRIMARY KEY,
                    full_name TEXT,
                    email TEXT,
                    avatar_url TEXT,
                    role TEXT NOT NULL DEFAULT 'agent',
                    theme TEXT NOT NULL DEFAULT 'system',
                    preferences TEXT NOT NULL DEFAULT '{"notifications": true, "simple_mode": true, "compact_view": false}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ticket_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
                    ml_topic TEXT,
                    ml_sentiment TEXT,
                    ml_confidence REAL,
                    topic_confidence REAL,
                    sentiment_confidence REAL,
                    llm_called INTEGER NOT NULL DEFAULT 0,
                    llm_succeeded INTEGER NOT NULL DEFAULT 0,
                    fallback_occurred INTEGER NOT NULL DEFAULT 0,
                    llm_urgency TEXT,
                    extracted_order_id TEXT,
                    extracted_product TEXT,
                    extracted_deadline TEXT,
                    rag_query TEXT,
                    rag_used INTEGER NOT NULL DEFAULT 0,
                    retrieved_faq_ids TEXT NOT NULL DEFAULT '[]',
                    used_faq_ids TEXT NOT NULL DEFAULT '[]',
                    retrieval_count INTEGER NOT NULL DEFAULT 0,
                    retrieval_latency_ms REAL,
                    embedding_query_ms REAL,
                    vector_search_ms REAL,
                    total_retrieval_ms REAL,
                    is_cold_retrieval INTEGER NOT NULL DEFAULT 0,
                    rag_error TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ticket_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL DEFAULT 'system',
                    details TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                );
                """
            )

            # Auto-migrate older SQLite databases missing user_id
            existing_cols = {col[1] for col in conn.execute("PRAGMA table_info(tickets)").fetchall()}
            if "user_id" not in existing_cols:
                conn.execute("ALTER TABLE tickets ADD COLUMN user_id TEXT;")

            conn.executescript(
                """
                CREATE INDEX IF NOT EXISTS idx_sqlite_tkt_id ON tickets(ticket_id);
                CREATE INDEX IF NOT EXISTS idx_sqlite_user_id ON tickets(user_id);
                CREATE INDEX IF NOT EXISTS idx_sqlite_status ON tickets(status);
                CREATE INDEX IF NOT EXISTS idx_sqlite_category ON tickets(category);
                CREATE INDEX IF NOT EXISTS idx_sqlite_priority ON tickets(priority);
                CREATE INDEX IF NOT EXISTS idx_sqlite_team ON tickets(assigned_team);
                CREATE INDEX IF NOT EXISTS idx_sqlite_idempotency ON tickets(idempotency_key);
                CREATE INDEX IF NOT EXISTS idx_sqlite_analysis_tkt ON ticket_analyses(ticket_id);
                CREATE INDEX IF NOT EXISTS idx_sqlite_events_tkt ON ticket_events(ticket_id);
                """
            )

    def find_by_idempotency_key(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        if not idempotency_key:
            return None
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM tickets WHERE idempotency_key = ?", (idempotency_key,)
            ).fetchone()
            return dict(row) if row else None

    def save_ticket(
        self,
        ticket_data: Dict[str, Any],
        analysis_data: Optional[Dict[str, Any]] = None,
        event_details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            # Ensure user_id column exists if table was created earlier without it
            cursor = conn.execute("PRAGMA table_info(tickets);")
            cols = [row["name"] for row in cursor.fetchall()]
            if "user_id" not in cols:
                conn.execute("ALTER TABLE tickets ADD COLUMN user_id TEXT;")

            conn.execute(
                """
                INSERT INTO tickets (
                    ticket_id, user_id, customer_name, customer_id, email, tier, subject,
                    status, priority, category, sentiment, confidence, assigned_team,
                    escalation_level, classification_source, generated_reply,
                    idempotency_key, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ticket_data.get("ticket_id"),
                    ticket_data.get("user_id"),
                    ticket_data.get("customer_name"),
                    ticket_data.get("customer_id"),
                    ticket_data.get("email"),
                    ticket_data.get("tier", "Bronze"),
                    ticket_data.get("subject"),
                    ticket_data.get("status", "open"),
                    ticket_data.get("priority", "Medium"),
                    ticket_data.get("category"),
                    ticket_data.get("sentiment"),
                    ticket_data.get("confidence"),
                    ticket_data.get("assigned_team"),
                    ticket_data.get("escalation_level", "Not Escalated"),
                    ticket_data.get("classification_source"),
                    ticket_data.get("generated_reply"),
                    ticket_data.get("idempotency_key"),
                    ticket_data.get("created_at") or now_iso,
                    ticket_data.get("updated_at") or now_iso,
                ),
            )

            if analysis_data:
                retrieved_faq_ids = json.dumps(analysis_data.get("retrieved_faq_ids", []))
                used_faq_ids = json.dumps(analysis_data.get("used_faq_ids", []))
                conn.execute(
                    """
                    INSERT INTO ticket_analyses (
                        ticket_id, ml_topic, ml_sentiment, ml_confidence,
                        topic_confidence, sentiment_confidence, llm_called,
                        llm_succeeded, fallback_occurred, llm_urgency,
                        extracted_order_id, extracted_product, extracted_deadline,
                        rag_query, rag_used, retrieved_faq_ids, used_faq_ids,
                        retrieval_count, retrieval_latency_ms, embedding_query_ms,
                        vector_search_ms, total_retrieval_ms, is_cold_retrieval,
                        rag_error, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ticket_data.get("ticket_id"),
                        analysis_data.get("ml_topic"),
                        analysis_data.get("ml_sentiment"),
                        analysis_data.get("ml_confidence"),
                        analysis_data.get("topic_confidence"),
                        analysis_data.get("sentiment_confidence"),
                        1 if analysis_data.get("llm_called") else 0,
                        1 if analysis_data.get("llm_succeeded") else 0,
                        1 if analysis_data.get("fallback_occurred") else 0,
                        analysis_data.get("llm_urgency"),
                        analysis_data.get("extracted_order_id"),
                        analysis_data.get("extracted_product"),
                        analysis_data.get("extracted_deadline"),
                        analysis_data.get("rag_query"),
                        1 if analysis_data.get("rag_used") else 0,
                        retrieved_faq_ids,
                        used_faq_ids,
                        analysis_data.get("retrieval_count", 0),
                        analysis_data.get("retrieval_latency_ms"),
                        analysis_data.get("embedding_query_ms"),
                        analysis_data.get("vector_search_ms"),
                        analysis_data.get("total_retrieval_ms"),
                        1 if analysis_data.get("is_cold_retrieval") else 0,
                        analysis_data.get("rag_error"),
                        analysis_data.get("created_at") or now_iso,
                    ),
                )

            # Record Creation Event
            event_payload = json.dumps(event_details or {"action": "ticket_created"})
            conn.execute(
                """
                INSERT INTO ticket_events (ticket_id, event_type, actor, details, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (ticket_data.get("ticket_id"), "ticket_created", "system", event_payload, now_iso),
            )
            conn.commit()

        return self.get_ticket(ticket_data.get("ticket_id")) or ticket_data

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)).fetchone()
            if not row:
                return None
            res = dict(row)
            return res

    def list_tickets(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_team: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        user_id: Optional[str] = None,
        exclude_benchmarks: bool = True,
    ) -> Tuple[List[Dict[str, Any]], int]:
        conditions = []
        params = []

        if exclude_benchmarks:
            conditions.append("(customer_name != 'Scenario Test' OR customer_name IS NULL)")
        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
        if status:
            conditions.append("status = ?")
            params.append(status)
        if category:
            conditions.append("category = ?")
            params.append(category)
        if priority:
            conditions.append("priority = ?")
            params.append(priority)
        if assigned_team:
            conditions.append("assigned_team = ?")
            params.append(assigned_team)
        if search:
            conditions.append("(ticket_id LIKE ? OR subject LIKE ? OR customer_name LIKE ?)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        offset = max(0, (page - 1) * limit)

        with self._get_connection() as conn:
            count_query = f"SELECT COUNT(*) FROM tickets{where_clause}"
            total = conn.execute(count_query, params).fetchone()[0]

            query = f"""
                SELECT * FROM tickets{where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            rows = conn.execute(query, params + [limit, offset]).fetchall()
            items = [dict(r) for r in rows]

        return items, total

    def update_ticket(
        self,
        ticket_id: str,
        updates: Dict[str, Any],
        actor: str = "agent",
    ) -> Optional[Dict[str, Any]]:
        current = self.get_ticket(ticket_id)
        if not current:
            return None

        allowed_fields = {"status", "assigned_team", "priority", "escalation_level", "user_id"}
        valid_updates = {k: v for k, v in updates.items() if k in allowed_fields and v is not None}
        if not valid_updates:
            return current

        valid_updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        set_clauses = [f"{k} = ?" for k in valid_updates.keys()]
        params = list(valid_updates.values()) + [ticket_id]

        with self._get_connection() as conn:
            conn.execute(f"UPDATE tickets SET {', '.join(set_clauses)} WHERE ticket_id = ?", params)
            # Log audit event
            event_payload = json.dumps({"previous": {k: current.get(k) for k in valid_updates}, "updated": valid_updates})
            conn.execute(
                """
                INSERT INTO ticket_events (ticket_id, event_type, actor, details, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (ticket_id, "ticket_updated", actor, event_payload, valid_updates["updated_at"]),
            )
            conn.commit()

        return self.get_ticket(ticket_id)

    def get_ticket_analysis(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM ticket_analyses WHERE ticket_id = ? ORDER BY id DESC LIMIT 1",
                (ticket_id,),
            ).fetchone()
            if not row:
                return None
            res = dict(row)
            try:
                res["retrieved_faq_ids"] = json.loads(res.get("retrieved_faq_ids") or "[]")
            except Exception:
                res["retrieved_faq_ids"] = []
            try:
                res["used_faq_ids"] = json.loads(res.get("used_faq_ids") or "[]")
            except Exception:
                res["used_faq_ids"] = []
            return res

    def get_ticket_events(self, ticket_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM ticket_events WHERE ticket_id = ? ORDER BY created_at ASC",
                (ticket_id,),
            ).fetchall()
            events = []
            for r in rows:
                item = dict(r)
                try:
                    item["details"] = json.loads(item.get("details") or "{}")
                except Exception:
                    item["details"] = {}
                events.append(item)
            return events

    def get_analytics(
        self,
        user_id: Optional[str] = None,
        exclude_benchmarks: bool = True,
    ) -> Dict[str, Any]:
        if user_id == "__none__":
            return {
                "total_tickets": 0,
                "open_tickets": 0,
                "in_progress_tickets": 0,
                "resolved_tickets": 0,
                "escalated_tickets": 0,
                "high_priority_tickets": 0,
                "category_distribution": {},
                "priority_distribution": {},
                "sentiment_distribution": {},
                "team_distribution": {},
                "storage_backend": self.backend_name,
            }

        conditions = []
        params: List[Any] = []
        if exclude_benchmarks:
            conditions.append("(customer_name != 'Scenario Test' OR customer_name IS NULL)")
        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)

        base_where = " WHERE " + " AND ".join(conditions) if conditions else ""

        def build_clause(extra: str = ""):
            if not base_where:
                return f" WHERE {extra}" if extra else ""
            return f"{base_where} AND {extra}" if extra else base_where

        with self._get_connection() as conn:
            total_tickets = conn.execute(f"SELECT COUNT(*) FROM tickets{base_where}", params).fetchone()[0]
            open_count = conn.execute(f"SELECT COUNT(*) FROM tickets{build_clause('status = ?')}", params + ["open"]).fetchone()[0]
            resolved_count = conn.execute(f"SELECT COUNT(*) FROM tickets{build_clause('status = ?')}", params + ["resolved"]).fetchone()[0]
            in_progress_count = conn.execute(f"SELECT COUNT(*) FROM tickets{build_clause('status = ?')}", params + ["in_progress"]).fetchone()[0]
            escalation_extra = "(escalation_level != 'Not Escalated' OR status = 'escalated')"
            escalated_count = conn.execute(
                f"SELECT COUNT(*) FROM tickets{build_clause(escalation_extra)}",
                params,
            ).fetchone()[0]
            high_priority_count = conn.execute(f"SELECT COUNT(*) FROM tickets{build_clause('priority = ?')}", params + ["High"]).fetchone()[0]

            cat_rows = conn.execute(f"SELECT category, COUNT(*) FROM tickets{base_where} GROUP BY category", params).fetchall()
            category_distribution = {r[0] or "unassigned": r[1] for r in cat_rows}

            prio_rows = conn.execute(f"SELECT priority, COUNT(*) FROM tickets{base_where} GROUP BY priority", params).fetchall()
            priority_distribution = {r[0]: r[1] for r in prio_rows}

            sent_rows = conn.execute(f"SELECT sentiment, COUNT(*) FROM tickets{base_where} GROUP BY sentiment", params).fetchall()
            sentiment_distribution = {r[0] or "UNKNOWN": r[1] for r in sent_rows}

            team_rows = conn.execute(f"SELECT assigned_team, COUNT(*) FROM tickets{base_where} GROUP BY assigned_team", params).fetchall()
            team_distribution = {r[0] or "Unassigned": r[1] for r in team_rows}

        return {
            "total_tickets": total_tickets,
            "open_tickets": open_count,
            "in_progress_tickets": in_progress_count,
            "resolved_tickets": resolved_count,
            "escalated_tickets": escalated_count,
            "high_priority_tickets": high_priority_count,
            "category_distribution": category_distribution,
            "priority_distribution": priority_distribution,
            "sentiment_distribution": sentiment_distribution,
            "team_distribution": team_distribution,
            "storage_backend": self.backend_name,
        }

    def check_health(self) -> Dict[str, Any]:
        try:
            with self._get_connection() as conn:
                count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
            return {"status": "ok", "backend": self.backend_name, "ticket_count": count}
        except Exception as e:
            return {"status": "error", "backend": self.backend_name, "error": str(e)}

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM profiles WHERE id = ?", (user_id,)).fetchone()
            if not row:
                return None
            res = dict(row)
            if isinstance(res.get("preferences"), str):
                try:
                    res["preferences"] = json.loads(res["preferences"])
                except Exception:
                    res["preferences"] = {}
            return res

    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        current = self.get_user_profile(user_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        allowed = {"full_name", "avatar_url", "theme", "preferences"}
        valid = {k: v for k, v in updates.items() if k in allowed}
        if not current:
            # Create default profile if not exists
            prefs = valid.get("preferences") or {"notifications": True, "simple_mode": True, "compact_view": False}
            if not isinstance(prefs, str):
                prefs = json.dumps(prefs)
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO profiles (id, full_name, email, avatar_url, role, theme, preferences, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        valid.get("full_name") or updates.get("email", "").split("@")[0] or "User",
                        updates.get("email", ""),
                        valid.get("avatar_url") or "",
                        "agent",
                        valid.get("theme") or "system",
                        prefs,
                        now_iso,
                        now_iso,
                    ),
                )
                conn.commit()
            return self.get_user_profile(user_id)

        if not valid:
            return current

        if "preferences" in valid and isinstance(valid["preferences"], (dict, list)):
            valid["preferences"] = json.dumps(valid["preferences"])

        valid["updated_at"] = now_iso
        set_clauses = [f"{k} = ?" for k in valid.keys()]
        params = list(valid.values()) + [user_id]
        with self._get_connection() as conn:
            conn.execute(f"UPDATE profiles SET {', '.join(set_clauses)} WHERE id = ?", params)
            conn.commit()
        return self.get_user_profile(user_id)

    def update_user_role_admin(self, target_user_id: str, new_role: str) -> Optional[Dict[str, Any]]:
        if new_role not in ("admin", "manager", "agent"):
            raise ValueError(f"Invalid role: {new_role}")
        now_iso = datetime.now(timezone.utc).isoformat()
        current = self.get_user_profile(target_user_id)
        if not current:
            # Create default profile with specified role
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO profiles (id, full_name, email, avatar_url, role, theme, preferences, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (target_user_id, "User", "", "", new_role, "system", "{}", now_iso, now_iso),
                )
                conn.commit()
            return self.get_user_profile(target_user_id)

        with self._get_connection() as conn:
            conn.execute("UPDATE profiles SET role = ?, updated_at = ? WHERE id = ?", (new_role, now_iso, target_user_id))
            conn.commit()
        return self.get_user_profile(target_user_id)

    def bootstrap_first_admin(self, admin_email: str) -> str:
        with self._get_connection() as conn:
            admin_count = conn.execute("SELECT COUNT(*) FROM profiles WHERE role = 'admin'").fetchone()[0]
            if admin_count > 0:
                raise ValueError("An administrator already exists. Bootstrap procedure is permanently locked.")
            row = conn.execute("SELECT id FROM profiles WHERE email = ?", (admin_email,)).fetchone()
            if not row:
                raise ValueError(f'User profile with email "{admin_email}" does not exist. Please sign up first.')
            target_id = row["id"]
            now_iso = datetime.now(timezone.utc).isoformat()
            conn.execute("UPDATE profiles SET role = 'admin', updated_at = ? WHERE id = ?", (now_iso, target_id))
            conn.commit()
            return f"Success: {admin_email} has been promoted to initial Administrator."



class SupabaseRepository(BaseRepository):
    """Supabase PostgreSQL implementation via official supabase client."""

    backend_name: str = "supabase"

    def __init__(self, supabase_url: str, supabase_key: str):
        from supabase import create_client, Client
        self.supabase_url = supabase_url
        self.client: Client = create_client(supabase_url, supabase_key)
        logger.info(f"Initialized SupabaseRepository connected to {supabase_url[:20]}...")

    def find_by_idempotency_key(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        if not idempotency_key:
            return None
        res = self.client.table("tickets").select("*").eq("idempotency_key", idempotency_key).limit(1).execute()
        return res.data[0] if res.data else None

    def save_ticket(
        self,
        ticket_data: Dict[str, Any],
        analysis_data: Optional[Dict[str, Any]] = None,
        event_details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()
        user_id = ticket_data.get("user_id")
        if user_id:
            try:
                import uuid
                uuid.UUID(str(user_id))
            except (ValueError, TypeError, AttributeError):
                user_id = None

        tkt_payload = {
            "ticket_id": ticket_data.get("ticket_id"),
            "user_id": user_id,
            "customer_name": ticket_data.get("customer_name"),
            "customer_id": ticket_data.get("customer_id"),
            "email": ticket_data.get("email"),
            "tier": ticket_data.get("tier", "Bronze"),
            "subject": ticket_data.get("subject"),
            "status": ticket_data.get("status", "open"),
            "priority": ticket_data.get("priority", "Medium"),
            "category": ticket_data.get("category"),
            "sentiment": ticket_data.get("sentiment"),
            "confidence": ticket_data.get("confidence"),
            "assigned_team": ticket_data.get("assigned_team"),
            "escalation_level": ticket_data.get("escalation_level", "Not Escalated"),
            "classification_source": ticket_data.get("classification_source"),
            "generated_reply": ticket_data.get("generated_reply"),
            "idempotency_key": ticket_data.get("idempotency_key"),
            "created_at": ticket_data.get("created_at") or now_iso,
            "updated_at": ticket_data.get("updated_at") or now_iso,
        }
        res = self.client.table("tickets").insert(tkt_payload).execute()
        saved = res.data[0] if res.data else tkt_payload

        if analysis_data:
            analysis_payload = {
                "ticket_id": ticket_data.get("ticket_id"),
                "ml_topic": analysis_data.get("ml_topic"),
                "ml_sentiment": analysis_data.get("ml_sentiment"),
                "ml_confidence": analysis_data.get("ml_confidence"),
                "topic_confidence": analysis_data.get("topic_confidence"),
                "sentiment_confidence": analysis_data.get("sentiment_confidence"),
                "llm_called": bool(analysis_data.get("llm_called")),
                "llm_succeeded": bool(analysis_data.get("llm_succeeded")),
                "fallback_occurred": bool(analysis_data.get("fallback_occurred")),
                "llm_urgency": analysis_data.get("llm_urgency"),
                "extracted_order_id": analysis_data.get("extracted_order_id"),
                "extracted_product": analysis_data.get("extracted_product"),
                "extracted_deadline": analysis_data.get("extracted_deadline"),
                "rag_query": analysis_data.get("rag_query"),
                "rag_used": bool(analysis_data.get("rag_used")),
                "retrieved_faq_ids": analysis_data.get("retrieved_faq_ids", []),
                "used_faq_ids": analysis_data.get("used_faq_ids", []),
                "retrieval_count": analysis_data.get("retrieval_count", 0),
                "retrieval_latency_ms": analysis_data.get("retrieval_latency_ms"),
                "embedding_query_ms": analysis_data.get("embedding_query_ms"),
                "vector_search_ms": analysis_data.get("vector_search_ms"),
                "total_retrieval_ms": analysis_data.get("total_retrieval_ms"),
                "is_cold_retrieval": bool(analysis_data.get("is_cold_retrieval")),
                "rag_error": analysis_data.get("rag_error"),
                "created_at": analysis_data.get("created_at") or now_iso,
            }
            self.client.table("ticket_analyses").insert(analysis_payload).execute()

        event_payload = {
            "ticket_id": ticket_data.get("ticket_id"),
            "event_type": "ticket_created",
            "actor": "system",
            "details": event_details or {"action": "ticket_created"},
            "created_at": now_iso,
        }
        self.client.table("ticket_events").insert(event_payload).execute()

        return saved

    def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        res = self.client.table("tickets").select("*").eq("ticket_id", ticket_id).limit(1).execute()
        return res.data[0] if res.data else None

    def list_tickets(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_team: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
        user_id: Optional[str] = None,
        exclude_benchmarks: bool = True,
    ) -> Tuple[List[Dict[str, Any]], int]:
        query = self.client.table("tickets").select("*", count="exact")
        if exclude_benchmarks:
            query = query.neq("customer_name", "Scenario Test")
        if user_id:
            query = query.eq("user_id", user_id)
        if status:
            query = query.eq("status", status)
        if category:
            query = query.eq("category", category)
        if priority:
            query = query.eq("priority", priority)
        if assigned_team:
            query = query.eq("assigned_team", assigned_team)
        if search:
            query = query.ilike("subject", f"%{search}%")

        offset = max(0, (page - 1) * limit)
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        res = query.execute()
        return res.data or [], res.count or len(res.data or [])

    def update_ticket(
        self,
        ticket_id: str,
        updates: Dict[str, Any],
        actor: str = "agent",
    ) -> Optional[Dict[str, Any]]:
        current = self.get_ticket(ticket_id)
        if not current:
            return None

        allowed_fields = {"status", "assigned_team", "priority", "escalation_level", "user_id"}
        valid_updates = {k: v for k, v in updates.items() if k in allowed_fields and v is not None}
        if not valid_updates:
            return current

        if "user_id" in valid_updates and valid_updates["user_id"]:
            try:
                import uuid
                uuid.UUID(str(valid_updates["user_id"]))
            except (ValueError, TypeError, AttributeError):
                valid_updates["user_id"] = None

        valid_updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        res = self.client.table("tickets").update(valid_updates).eq("ticket_id", ticket_id).execute()

        event_payload = {
            "ticket_id": ticket_id,
            "event_type": "ticket_updated",
            "actor": actor,
            "details": {"previous": {k: current.get(k) for k in valid_updates}, "updated": valid_updates},
            "created_at": valid_updates["updated_at"],
        }
        self.client.table("ticket_events").insert(event_payload).execute()

        return res.data[0] if res.data else self.get_ticket(ticket_id)

    def get_ticket_analysis(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        res = (
            self.client.table("ticket_analyses")
            .select("*")
            .eq("ticket_id", ticket_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        return res.data[0] if res.data else None

    def get_ticket_events(self, ticket_id: str) -> List[Dict[str, Any]]:
        res = (
            self.client.table("ticket_events")
            .select("*")
            .eq("ticket_id", ticket_id)
            .order("created_at", desc=False)
            .execute()
        )
        return res.data or []

    def get_analytics(
        self,
        user_id: Optional[str] = None,
        exclude_benchmarks: bool = True,
    ) -> Dict[str, Any]:
        if user_id == "__none__":
            return {
                "total_tickets": 0,
                "open_tickets": 0,
                "in_progress_tickets": 0,
                "resolved_tickets": 0,
                "escalated_tickets": 0,
                "high_priority_tickets": 0,
                "category_distribution": {},
                "priority_distribution": {},
                "sentiment_distribution": {},
                "team_distribution": {},
                "storage_backend": self.backend_name,
            }

        # Query ticket stats with user scoping
        query = self.client.table("tickets").select("status,priority,category,sentiment,assigned_team,escalation_level,customer_name,user_id")
        if exclude_benchmarks:
            query = query.neq("customer_name", "Scenario Test")
        if user_id:
            query = query.eq("user_id", user_id)
        all_tickets_res = query.execute()
        rows = all_tickets_res.data or []

        total = len(rows)
        open_c = sum(1 for r in rows if r.get("status") == "open")
        resolved_c = sum(1 for r in rows if r.get("status") == "resolved")
        in_progress_c = sum(1 for r in rows if r.get("status") == "in_progress")
        escalated_c = sum(
            1 for r in rows if r.get("escalation_level") != "Not Escalated" or r.get("status") == "escalated"
        )
        high_prio_c = sum(1 for r in rows if r.get("priority") == "High")

        cat_dist: Dict[str, int] = {}
        prio_dist: Dict[str, int] = {}
        sent_dist: Dict[str, int] = {}
        team_dist: Dict[str, int] = {}

        for r in rows:
            cat = r.get("category") or "unassigned"
            cat_dist[cat] = cat_dist.get(cat, 0) + 1

            prio = r.get("priority") or "Medium"
            prio_dist[prio] = prio_dist.get(prio, 0) + 1

            sent = r.get("sentiment") or "UNKNOWN"
            sent_dist[sent] = sent_dist.get(sent, 0) + 1

            team = r.get("assigned_team") or "Unassigned"
            team_dist[team] = team_dist.get(team, 0) + 1

        return {
            "total_tickets": total,
            "open_tickets": open_c,
            "in_progress_tickets": in_progress_c,
            "resolved_tickets": resolved_c,
            "escalated_tickets": escalated_c,
            "high_priority_tickets": high_prio_c,
            "category_distribution": cat_dist,
            "priority_distribution": prio_dist,
            "sentiment_distribution": sent_dist,
            "team_distribution": team_dist,
            "storage_backend": self.backend_name,
        }

    def check_health(self) -> Dict[str, Any]:
        try:
            res = self.client.table("tickets").select("count", count="exact").limit(1).execute()
            return {"status": "ok", "backend": self.backend_name, "ticket_count": res.count or 0}
        except Exception as e:
            return {"status": "error", "backend": self.backend_name, "error": str(e)}

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            res = self.client.table("profiles").select("*").eq("id", user_id).limit(1).execute()
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Error fetching profile for {user_id} from Supabase: {e}")
            return None

    def update_user_profile(self, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        allowed = {"full_name", "avatar_url", "theme", "preferences"}
        valid = {k: v for k, v in updates.items() if k in allowed}
        if not valid:
            return self.get_user_profile(user_id)
        valid["updated_at"] = datetime.now(timezone.utc).isoformat()
        try:
            res = self.client.table("profiles").update(valid).eq("id", user_id).execute()
            if res.data:
                return res.data[0]
            # If not yet created, insert
            valid["id"] = user_id
            valid["role"] = "agent"
            valid["email"] = updates.get("email", "")
            valid["created_at"] = valid["updated_at"]
            ins_res = self.client.table("profiles").insert(valid).execute()
            return ins_res.data[0] if ins_res.data else self.get_user_profile(user_id)
        except Exception as e:
            logger.error(f"Error updating profile for {user_id} in Supabase: {e}")
            return None

    def update_user_role_admin(self, target_user_id: str, new_role: str) -> Optional[Dict[str, Any]]:
        if new_role not in ("admin", "manager", "agent"):
            raise ValueError(f"Invalid role: {new_role}")
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            res = self.client.table("profiles").update({"role": new_role, "updated_at": now_iso}).eq("id", target_user_id).execute()
            return res.data[0] if res.data else self.get_user_profile(target_user_id)
        except Exception as e:
            logger.error(f"Error updating role for {target_user_id} in Supabase: {e}")
            return None

    def bootstrap_first_admin(self, admin_email: str) -> str:
        try:
            res = self.client.rpc("bootstrap_first_admin", {"admin_email": admin_email}).execute()
            return str(res.data)
        except Exception as e:
            logger.error(f"Error executing bootstrap_first_admin in Supabase: {e}")
            raise



_repo_instance: Optional[BaseRepository] = None


def get_repository(force_refresh: bool = False) -> BaseRepository:
    """
    Factory function to retrieve the persistent repository.
    Prioritizes Supabase if SUPABASE_URL and SUPABASE_KEY are provided and functional.
    Otherwise gracefully falls back to persistent SQLite.
    """
    global _repo_instance
    if _repo_instance is not None and not force_refresh:
        return _repo_instance

    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_key = os.getenv("SUPABASE_KEY", "").strip()
    use_local_force = os.getenv("USE_LOCAL_DB", "").lower() in ("true", "1", "yes")

    if supabase_url and supabase_key and not use_local_force:
        if supabase_key.startswith("sb_publishable_"):
            logger.info(
                "Supabase client publishable key detected (client anon key). "
                "Server repository using persistent SQLite to honor database RLS policies."
            )
        else:
            try:
                logger.info("Attempting connection to Supabase PostgreSQL...")
                repo = SupabaseRepository(supabase_url=supabase_url, supabase_key=supabase_key)
                health = repo.check_health()
                if health["status"] == "ok":
                    logger.info("Supabase connection verified successfully.")
                    _repo_instance = repo
                    return _repo_instance
                else:
                    logger.warning(
                        f"Supabase connection test failed: {health.get('error')}. Falling back to SQLite local database."
                    )
            except Exception as exc:
                logger.warning(
                    f"Failed to initialize Supabase client ({exc}). Falling back to SQLite local database."
                )

    raw_path = os.getenv("SQLITE_DB_PATH", "data/tickets_dev.db")
    if raw_path != ":memory:" and not os.path.isabs(raw_path):
        candidate_backend = _base_dir / raw_path
        candidate_root = _base_dir.parent / raw_path
        if candidate_backend.exists():
            resolved_db = str(candidate_backend)
        elif candidate_root.exists():
            resolved_db = str(candidate_root)
        else:
            resolved_db = str(candidate_backend)
    else:
        resolved_db = raw_path

    logger.info(f"Using SQLite local development database at {resolved_db}")
    _repo_instance = SQLiteRepository(db_path=resolved_db)
    return _repo_instance


def set_repository(repo: BaseRepository) -> None:
    """Explicitly override the repository instance (primarily for tests)."""
    global _repo_instance
    _repo_instance = repo
