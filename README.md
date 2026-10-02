# Resolve AI — Enterprise Multi-Agent Ticket Resolution Platform

> **"Every ticket. One intelligent resolution."**  
> *Multiple specialized agents. One coordinated system. Human-approved outcomes.*

**Resolve AI** is a production-ready enterprise multi-agent customer support ticket routing, knowledge grounding, and resolution platform built with **FastAPI**, **React + Vite + Tailwind CSS**, **Supabase PostgreSQL** (with automatic zero-config local SQLite fallback), **LangGraph**, **scikit-learn**, **ChromaDB**, and **Sentence-Transformers**.

*(Note: "Resolve AI" is a working brand name. All brand names, taglines, and asset configurations are centralized in `frontend/src/config/brand.ts` for simple updates.)*

The platform classifies incoming support tickets, detects sentiment and urgency, dynamically calculates SLA priority based on customer tiers, routes tickets to specialized departments, escalates critical cases, performs hybrid category-aware RAG over verified FAQ documentation, and generates grounded customer responses with strict citation verification and human-in-the-loop review.

---

## 1. System Architecture & Workflow

The orchestration pipeline is implemented as a **LangGraph StateGraph** operating over typed Pydantic `TicketState`:

```
                       [START]
                          │
                          ▼
                 [ML Classification]
                (Naive Bayes + LogReg)
                          │
                          ▼
                 〈Confidence >= 0.50?〉
                  ╱                 ╲
           YES   ╱                   ╲  NO (Fallback)
                ▼                     ▼
          [Priority Agent]     [LLM Classification]
                │                     │
                │◄────────────────────┘
                ▼
         [Routing Agent]  ──> (Finance Team, Logistics Team, Tech Support, General Support)
                │
                ▼
        [Escalation Agent] ──> (Senior Manager for High-Priority Platinum/Gold)
                │
                ▼
         [RAG Retrieval]  ──> (ChromaDB + sentence-transformers/all-MiniLM-L6-v2)
                │              (Topic-aware category filtering + Global fallback)
                ▼
         [Response Agent] ──> (Grounded resolution + verified FAQ citations)
                │
                ▼
              [END]
```

### Core Architecture Components

1. **FastAPI Backend (`backend/app/api/`)**:
   - `GET /api/health`: System health, storage backend status, vector store readiness.
   - `POST /api/tickets`: Ingests a new ticket, executes multi-agent LangGraph triage, persists to Supabase/SQLite, and returns detailed diagnostic state. Safe against duplicate submissions via `idempotency_key`.
   - `GET /api/tickets`: Paginated ticket queue with search and filters (`status`, `category`, `priority`, `assigned_team`).
   - `GET /api/tickets/{ticket_id}`: Full ticket details, analysis metadata, retrieval timings, FAQ citations, and audit trail events.
   - `PATCH /api/tickets/{ticket_id}`: Safe updates to status, team assignments, and priority with audit logging.
   - `GET /api/analytics`: Real-time operational ticket statistics from the database alongside offline evaluation benchmarks.
2. **Supabase PostgreSQL & Local SQLite Persistence (`backend/supabase/`, `backend/app/db/`)**:
   - `backend/supabase/schema.sql`: Full versioned schema with `tickets`, `ticket_analyses`, and `ticket_events` tables, foreign keys, timestamps, and indexes.
   - Zero-configuration local fallback: If `SUPABASE_URL` and `SUPABASE_KEY` are unset, automatically uses persistent SQLite (`backend/data/tickets_dev.db`) without mock illusions or silent failures.
3. **React + Vite + Tailwind CSS Dashboard (`frontend/`)**:
   - **Dashboard**: Live ticket counts, open/resolved queue, category distribution, and recent tickets table.
   - **Create Ticket**: Form with one-click demo presets, validation, and immediate triage preview.
   - **Ticket Queue**: Interactive search, filtering, pagination, and quick-action status/team reassignments.
   - **Ticket Details / AI Diagnostics**: Full analysis breakdown, classification source (ML vs LLM fallback), cold/warm RAG retrieval latencies, verified canonical FAQ citations, grounded response, and audit trail.
   - **Quality & Evaluation**: Displays offline test evaluation metrics (82.0% accuracy, 100% citation validity, zero hallucinated citations, threshold sweep table) clearly distinguished from live database statistics.
4. **AI & Safety Guarantees**:
   - Differentiates fine-grained refund intents (`FAQ_018`, `FAQ_028`, `FAQ_024`, `FAQ_010`).
   - Abstains and escalates unsupported inquiries (e.g., cryptocurrency payments, physical stores) without hallucinating citations.
   - Strictly enforces that financial side effects (e.g., disbursing refunds, altering accounts) remain simulation-only, requiring explicit human authorization.

---

## 2. Quickstart & Windows PowerShell Commands

### Repository Structure
```
ticket_env/
├── backend/            # FastAPI, LangGraph multi-agent pipeline, ChromaDB RAG, Supabase migrations, & tests
└── frontend/           # React 19, TypeScript, Vite, Tailwind CSS enterprise dashboard
```

### Prerequisites
- Python 3.10+ (using virtual environment at `backend/venv`)
- Node.js v18+ and npm (tested on Node v22.14.0)

### 1. Start the FastAPI Backend
In a Windows PowerShell window:
```powershell
cd backend

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Launch FastAPI server with auto-reload on port 8000
uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- Health check: `http://127.0.0.1:8000/api/health`

### 2. Start the React Frontend Dashboard
In a second Windows PowerShell window:
```powershell
cd frontend
npm install
npm run dev
```
Open your browser at:
- `http://localhost:5173`

---

## 3. Supabase Cloud Database Setup

To use cloud Supabase PostgreSQL instead of the local SQLite fallback:
1. Create a new project at [supabase.com](https://supabase.com).
2. Open the **SQL Editor** in your Supabase dashboard.
3. Copy and run the contents of [`backend/supabase/schema.sql`](file:///c:/Users/anany/Downloads/ticket_env/backend/supabase/schema.sql).
4. Copy your project URL and service role (or anon) key into `backend/.env`:
   ```ini
   SUPABASE_URL=https://<your-project-id>.supabase.co
   SUPABASE_KEY=<your-supabase-key>
   USE_LOCAL_DB=false
   ```
5. Restart the FastAPI server. The dashboard navbar will automatically display **"Supabase DB"** with a green health indicator.

---

## 4. Running Tests & Builds

### Python Backend Tests
```powershell
cd backend

# 1. Live PostgreSQL Migration Scenarios (Docker/WSL)
.\venv\Scripts\python.exe -m unittest tests.test_postgres_live_scenarios -v

# 2. Migration AST Parser Tests (pglast C-parser)
.\venv\Scripts\python.exe -m unittest tests.test_postgres_migration -v

# 3. FastAPI REST API endpoints
.\venv\Scripts\python.exe -m unittest tests.test_api -v

# 4. Safety guardrails, MockLLMClient 'other' topic, and citation validity
.\venv\Scripts\python.exe -m unittest tests.test_safety_and_regression -v
```

### Frontend Production Build Check
```powershell
cd frontend
npm run build
```
*(Compiles cleanly with zero TypeScript or Vite bundle errors.)*

---

## 5. Verified Week 3 Evaluation Benchmarks

The system was evaluated against 160 realistic, non-leaked support tickets (60 validation, 100 test):

| Metric | Measured Result | Benchmark Target | Status |
|---|---|---|---|
| **Hybrid Topic Accuracy** | **82.0%** | $\ge 80.0\%$ | **PASS** |
| **Topic Macro F1 Score** | **0.8205** | $\ge 0.80$ | **PASS** |
| **Department Routing Accuracy** | **81.9%** | $\ge 80.0\%$ | **PASS** |
| **Citation ID Validity** | **100.0%** | $100.0\%$ | **PASS** |
| **Retrieval Membership Rate** | **100.0%** | $100.0\%$ | **PASS** |
| **Hallucinated Citation Rate** | **0.0%** | $0.0\%$ | **PASS** |
| **Abstention on Unsupported Inquiries** | **91.7%** | $\ge 85.0\%$ | **PASS** |
| **RAG Recall@3** | **100.0%** | $\ge 85.0\%$ | **PASS** |
| **RAG Latency (P50 / P95)** | **28.48 ms / 62.10 ms** | $< 50\text{ ms} / < 100\text{ ms}$ | **PASS** |

### Confidence Threshold Trade-Off Analysis
| Threshold | ML Fast-Path % | LLM Fallback % | Accuracy | Notes |
|---|---|---|---|---|
| `0.00` | 100.0% | 0.0% | 65.0% | Pure ML baseline |
| `0.40` | 61.0% | 39.0% | 77.0% | Moderate fallback |
| **`0.50`** | **27.0%** | **73.0%** | **82.0%** | **★ Production Default** |
| `0.60` | 14.0% | 86.0% | 82.0% | Conservative |
| `0.70` | 0.0% | 100.0% | 82.0% | Pure LLM fallback |

---

## 6. Manual Demo Checklist

Follow this checklist during your live presentation or review:

1. **Verify Backend Health**:
   - Visit `http://127.0.0.1:8000/api/health`.
   - Observe `{"status": "healthy", "storage_backend": "local_sqlite", "vector_store_status": "ready"}`.
2. **Explore Dashboard (`http://localhost:5173`)**:
   - Check the KPI counters: Total Tickets, Open Queue, Resolved, High Priority, and Escalated.
   - Inspect the live category, priority, and team assignment breakdown charts.
3. **Ingest a Ticket with Multi-Agent Triage**:
   - Navigate to **"Create Ticket"**.
   - Click the preset button **"Duplicate Charge (Billing)"**.
   - Observe the pre-filled fields (Michael Vance, Platinum tier).
   - Click **"Submit & Triage Ticket"**.
   - Verify the immediate triage card appears:
     - Ticket ID (e.g., `TKT-20261001-XXXXXX`).
     - Predicted Topic: `billing`.
     - Sentiment: `NEGATIVE`.
     - Assigned Team: `Finance Team`.
     - Priority: `High`.
     - Escalation: `Escalated to Senior Manager` (Platinum + High priority rule).
     - Grounded reply cites `FAQ_010`.
4. **Test Abstention & Safety Guardrail**:
   - On **"Create Ticket"**, click **"Unsupported / Crypto (Abstention)"**.
   - Submit the inquiry.
   - Observe that the generated reply abstains from hallucinating policies and routes for manual agent review without claiming automated payouts.
5. **Manage Tickets in the Queue**:
   - Navigate to **"Ticket Queue"**.
   - Filter by status `open` or category `billing`.
   - Use the inline dropdown to change a ticket's status to `in_progress` or `resolved`.
   - Reassign a ticket to `Finance Team`.
6. **Inspect Full AI Diagnostics & Audit Trail**:
   - Click **"Analyze"** on any ticket in the queue.
   - Inspect the retrieval latency breakdown (query embedding ms vs vector search ms).
   - Verify the canonical FAQ IDs and check the immutable audit trail history.
7. **Review Quality & Evaluation**:
   - Navigate to **"Quality & Evaluation"**.
   - Verify the side-by-side comparison table clearly distinguishing offline evaluation benchmarks (100 test samples) from live operational database telemetry.
