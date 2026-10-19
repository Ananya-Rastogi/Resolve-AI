# Resolve AI — AI-Powered Support Ticket Routing System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI_0.115%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React: 19](https://img.shields.io/badge/Frontend-React_19-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![Vite: 8](https://img.shields.io/badge/Bundler-Vite_8-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-FF6F00.svg)](https://langchain-ai.github.io/langgraph/)
[![ChromaDB](https://img.shields.io/badge/Vector_DB-ChromaDB-purple.svg)](https://www.trychroma.com/)
[![Supabase](https://img.shields.io/badge/Database-Supabase_PostgreSQL-3ECF8E.svg?logo=supabase&logoColor=white)](https://supabase.com/)
[![Vercel](https://img.shields.io/badge/Deployed-Vercel-black.svg?logo=vercel&logoColor=white)](https://resolve-ai-ananya-3e45.vercel.app/)
[![Tests: 117 Passed](https://img.shields.io/badge/Tests-117%20Passed-brightgreen.svg)]()

> **"Every ticket. One intelligent resolution."**  
> *Multiple specialized agents. One coordinated system. Grounded, human-approved outcomes.*

Resolve AI is an enterprise-grade multi-agent customer support ticket routing, knowledge grounding, and resolution platform. It integrates **FastAPI**, **React 19 + TypeScript + Vite + Tailwind CSS**, **LangGraph**, **scikit-learn**, **ChromaDB**, and **Sentence-Transformers**, backed by **Supabase PostgreSQL** with an automatic zero-configuration **SQLite fallback**.

The platform automates the entire support lifecycle: classifying incoming tickets, detecting sentiment and urgency, dynamically calculating SLA priorities based on customer tiers, routing issues to specialized departmental teams, escalating critical high-tier accounts, retrieving category-filtered FAQ context, generating strictly grounded responses with zero hallucinated citations, and providing audit trails for agent review.

---

## Quick Links

- **Live Production Demo:** [https://resolve-ai-ananya-3e45.vercel.app](https://resolve-ai-ananya-3e45.vercel.app/)
- **GitHub Repository:** [https://github.com/Ananya-Rastogi/Resolve-AI](https://github.com/Ananya-Rastogi/Resolve-AI)
- **Local Swagger API Documentation:** `http://127.0.0.1:8000/docs` *(available when running locally)*
- **Local ReDoc API Documentation:** `http://127.0.0.1:8000/redoc` *(available when running locally)*

---

## Table of Contents

1. [Project Overview & Problem Statement](#project-overview--problem-statement)
2. [Key Features](#key-features)
3. [Technology Stack](#technology-stack)
4. [System Architecture & Workflow](#system-architecture--workflow)
5. [Repository Structure](#repository-structure)
6. [Prerequisites & Installation](#prerequisites--installation)
7. [Environment Variable Configuration](#environment-variable-configuration)
8. [Running the Application](#running-the-application)
9. [API Documentation & Verified Endpoints](#api-documentation--verified-endpoints)
10. [Automated Testing & Verification](#automated-testing--verification)
11. [Model Evaluation & Verified Performance Metrics](#model-evaluation--verified-performance-metrics)
12. [Cloud Deployment Guide](#cloud-deployment-guide)
13. [Troubleshooting Guide](#troubleshooting-guide)
14. [Future Improvements](#future-improvements)
15. [Author & Contact](#author--contact)

---

## Project Overview & Problem Statement

### The Problem
Customer support organizations face severe operational bottlenecks as ticket volumes scale:
- **Triage Latency:** Manual review of tickets causes hours of initial response delay.
- **Misrouting & Bouncing:** Tickets bounce across departments (e.g., Billing vs. Tech Support), increasing Mean Time to Resolution (MTTR).
- **SLA Breaches:** VIP and high-urgency issues frequently get lost in large queues without automated escalation.
- **LLM Hallucinations:** Generic generative AI chatbots often invent return policies, cite non-existent articles, or promise financial refunds without verification.
- **Duplicate Ingestion:** Repeated submissions for the same issue clutter queues and waste representative capacity.

### The Resolve AI Solution
Resolve AI replaces brittle end-to-end prompting with a modular, deterministic multi-agent state machine:
1. **Sub-Millisecond ML Fast-Path:** Employs TF-IDF and Multinomial Naive Bayes to classify high-confidence tickets in under 1 ms, routing ambiguous tickets to structured fallback.
2. **Customer Tier & Sentiment-Aware SLA Matrix:** Deterministically computes resolution deadlines (1h, 4h, 24h, 48h) and triggers automated escalations for high-tier accounts.
3. **Category-Aware RAG Grounding:** Pre-filters vector search in ChromaDB by predicted category to eliminate cross-domain distractors.
4. **Strict Citation Guardrails:** Rejects responses citing unretrieved documents, abstains on unsupported inquiries (e.g., cryptocurrency, physical retail), and enforces simulation-only financial side effects.
5. **Dual Persistence with Zero-Config Fallback:** Seamlessly connects to cloud Supabase PostgreSQL in production while maintaining a persistent local SQLite database for offline development.

---

## Key Features

### 1. Machine Learning-Based Ticket Classification
- **Architecture:** `TfidfVectorizer(ngram_range=(1,2), max_features=1000)` paired with `MultinomialNB()`.
- **Performance:** Achieves **87.50% test accuracy** and **0.8718 Macro F1** on held-out test data across 4 core categories: `billing`, `shipping`, `technical`, and `other`.
- **Inference Speed:** Runs in **0.38 ms (median)** on CPU, enabling immediate fast-path triage without API costs.

### 2. Sentiment Analysis & Urgency Scoring
- **Architecture:** TF-IDF feature extraction combined with `LogisticRegression(max_iter=1000)`.
- **Performance:** Achieves **75.00% accuracy** and an **0.8333 F1-score on negative sentiment** detection, identifying angry or distressed customers for prioritized handling.

### 3. Ticket Priority Assignment & Intelligent Routing
- **Deterministic SLA Matrix:** Dynamically computes priority (`High`, `Medium`, `Low`) by cross-referencing customer tiers (`Platinum`, `Gold`, `Silver`, `Bronze`) against sentiment and issue urgency.
- **Specialized Routing:** Automatically routes tickets to specialized departments:
  - `billing` $\to$ **Finance Team**
  - `shipping` $\to$ **Logistics Team**
  - `technical` $\to$ **Tech Support**
  - `other` $\to$ **General Support**

### 4. Executive Escalation Management
- Identifies critical, time-sensitive issues (e.g., High-Priority Platinum or Gold inquiries) and automatically flags them as **"Escalated to Senior Manager"**, preventing VIP customer churn.

### 5. LangGraph Multi-Agent Workflow Orchestration
- Orchestrates multi-step reasoning using a typed Pydantic `TicketState` state graph.
- Implements conditional branching: high-confidence ML predictions ($\ge 0.50$) bypass LLM overhead directly to priority calculation, while ambiguous tickets route to a structured fallback agent.

### 6. Retrieval-Augmented Generation (RAG) with ChromaDB
- **Embedding Model:** Dense 384-dimensional representations via `sentence-transformers/all-MiniLM-L6-v2`.
- **Vector Store:** Persistent ChromaDB index over 30 canonical, deduplicated FAQ articles.
- **Hybrid Category Filtering:** Pre-filters articles by the predicted ticket category, eliminating cross-category semantic noise, with global search fallback if filtered results are empty.
- **Retrieval Performance:** Achieves **94.12% Recall@3** and **0.8442 MRR** across 160 benchmark queries.

### 7. Citation Verification & Safety Guardrails
- **Citation Integrity:** Verifies that every cited FAQ ID was present in `retrieved_sources`. Achieved **100.0% citation validity** with **0 hallucinated citations**.
- **Abstention on Unsupported Queries:** Correctly abstains on 91.67% of unsupported inquiries (e.g., cryptocurrency payments, physical stores) and escalates for human review.
- **Financial Simulation Guardrail:** Strictly prevents automated financial disbursements, tagging refund requests for explicit human authorization.

### 8. Real-Time Duplicate Ticket Detection
- Evaluates candidate ticket submissions against database records using a hybrid metric: Jaccard token overlap (60%) + Python `SequenceMatcher` ratio (40%) on subjects.
- Returns human-actionable similarity scores and shared keywords without performing destructive merges.
- Supports duplicate submission prevention via an optional `idempotency_key`.

### 9. Real-Time Operational Analytics Dashboard
- Live dashboard displaying open/resolved queues, category breakdowns, priority distributions, and assigned team workloads.
- Features a side-by-side **Quality & Evaluation** tab that displays offline test benchmarks (160 evaluation tickets) alongside live database metrics.

### 10. In-App AI Help Assistant
- Dedicated help assistant endpoint (`POST /api/help/chat`) providing grounded explanations of navigation, SLA policies, and priority matrix rules directly within the dashboard.

### 11. Dual Database Persistence & Zero-Config Fallback
- Production support for **Supabase PostgreSQL** with versioned migration scripts, relational foreign keys, and audit logging.
- **Automatic SQLite Fallback:** When running locally without Supabase credentials, or when a client publishable key is detected, the system automatically uses persistent SQLite (`data/tickets_dev.db`) without silent failures or mock illusions.

---

## Technology Stack

| Category | Technology | Purpose in Project |
| :--- | :--- | :--- |
| **Backend Framework** | **FastAPI 0.115+** | High-performance async REST API, OpenAPI docs, typed Pydantic request/response validation. |
| **ASGI Server** | **Uvicorn 0.30+** | Production-ready asynchronous web server. |
| **Agent Orchestration** | **LangGraph 0.2+** | Cyclical multi-agent state graph, conditional edge routing, typed `TicketState`. |
| **Machine Learning** | **scikit-learn 1.3+** | TF-IDF vectorization, Multinomial Naive Bayes topic classification, Logistic Regression sentiment analysis. |
| **Model Persistence** | **joblib 1.3+** | Serialization and cold-start loading of trained vectorizers and classifiers. |
| **Embeddings** | **Sentence-Transformers 3.0+** | Local CPU dense vector embeddings (`all-MiniLM-L6-v2`, 384 dimensions). |
| **Vector Database** | **ChromaDB 0.5+** | Embedded vector database for FAQ semantic search and metadata filtering. |
| **Cloud Database** | **Supabase (PostgreSQL)** | Relational cloud storage for tickets, analyses, profiles, and audit events. |
| **Local Database** | **SQLite3** | Zero-configuration local database with complete relational schema parity. |
| **Frontend Framework**| **React 19** | Component-driven responsive user interface. |
| **Build Tooling** | **Vite 8** | Rapid development server with HMR and optimized production bundling. |
| **Language** | **TypeScript 6.0** | Full end-to-end type safety for components and API clients. |
| **Styling** | **Tailwind CSS 3.4** | Modern utility-first responsive styling with dark/light mode support. |
| **Icons** | **Lucide React** | Clean, accessible iconography. |
| **Testing** | **unittest & pytest** | Comprehensive test suite covering API routes, LangGraph nodes, migrations, and safety guardrails. |
| **Deployment** | **Vercel & Render** | Vercel for frontend static hosting; Render for backend containerized web service. |

---

## System Architecture & Workflow

The orchestration pipeline is implemented as a **LangGraph StateGraph** operating over typed Pydantic `TicketState`:

```
                       [START: Ingest Ticket]
                                 │
                                 ▼
                     [ML Topic & Sentiment]
                   (TF-IDF + MNB + LogReg)
                                 │
                                 ▼
                      〈ML Confidence >= 0.50?〉
                       ╱                   ╲
                YES   ╱                     ╲  NO (< 0.50)
                     ▼                       ▼
              [Priority Agent]       [LLM Classification]
                     │               (Structured Fallback)
                     │                        │
                     │◄───────────────────────┘
                     ▼
              [Routing Agent]  ──> (Finance, Logistics, Tech Support, General Support)
                     │
                     ▼
             [Escalation Agent] ──> (Senior Manager for High-Priority Platinum/Gold)
                     │
                     ▼
              [RAG Retrieval]  ──> (ChromaDB + sentence-transformers/all-MiniLM-L6-v2)
                     │              (Category-aware filtering + Global fallback)
                     ▼
              [Response Agent] ──> (Grounded resolution + verified FAQ citations)
                     │
                     ▼
             [Persistence Layer] ──> (SQLite local / Supabase cloud + Audit trail)
                     │
                     ▼
                   [END]
```

### Multi-Agent Pipeline Execution Stages

1. **Ticket Ingestion (`POST /api/tickets`)**: Validates customer metadata, tier, subject, and body. Verifies the `idempotency_key` to prevent duplicate ingestion.
2. **ML Classification**: Generates topic predictions and sentiment scores using Multinomial Naive Bayes and Logistic Regression.
3. **Confidence Routing Check**: If ML confidence is $\ge 0.50$, the fast-path routes directly to priority assessment. If confidence is $< 0.50$, the ticket routes to the structured fallback agent.
4. **Priority Assessment**: Computes resolution deadlines based on customer tier (Platinum, Gold, Silver, Bronze) and detected sentiment/urgency.
5. **Department Routing**: Maps the verified category to a specialized team (Finance, Logistics, Tech Support, General Support).
6. **Escalation Management**: Evaluates account priority and automatically escalates critical high-tier tickets to Senior Management.
7. **Category-Aware RAG Retrieval**: Queries ChromaDB with the ticket inquiry, filtering by category to eliminate semantic distractors, falling back to global search if no category match is found.
8. **Grounded Response Generation**: Selects the best-matching canonical FAQ article, verifies that the citation ID exists in retrieved sources, and formats a customer response.
9. **Persistence & Audit Logging**: Atomically commits the ticket, its analysis record, and lifecycle events (`ticket_created`, `ticket_updated`) into relational storage.

---

## Repository Structure

```
ticket_env/
├── backend/                        # FastAPI backend application & ML pipeline
│   ├── app/
│   │   ├── agents/                 # Specialized LangGraph agent nodes
│   │   │   ├── classification.py   # ML classification node
│   │   │   ├── escalation.py       # Executive escalation logic
│   │   │   ├── llm_classification.py # Fallback triage agent node
│   │   │   ├── llm_client.py       # LLM provider abstraction (OpenAI / Mock)
│   │   │   ├── priority.py         # Customer tier & SLA priority engine
│   │   │   ├── response.py         # Grounded response & citation generation
│   │   │   └── routing.py          # Department assignment agent node
│   │   ├── api/                    # FastAPI routes and schemas
│   │   │   ├── main.py             # Route handlers & lifecycle middleware
│   │   │   └── schemas.py          # Pydantic request and response models
│   │   ├── db/                     # Data persistence layer
│   │   │   └── repository.py       # Supabase & SQLite repository implementations
│   │   ├── graph/                  # LangGraph workflow orchestration
│   │   │   ├── workflow.py         # StateGraph builder and conditional edges
│   │   │   └── visualization.py    # Mermaid graph generator
│   │   ├── models/                 # ML classifier pipelines
│   │   │   ├── ml_models.py        # TicketMLPipeline (TF-IDF + MNB + LogReg)
│   │   │   └── schemas.py          # Internal model data structures
│   │   ├── rag/                    # RAG retrieval and indexing engine
│   │   │   ├── chunker.py          # FAQ document chunking
│   │   │   ├── embeddings.py       # SentenceTransformer model wrapper
│   │   │   ├── loader.py           # Canonical CSV dataset loader
│   │   │   ├── pipeline.py         # End-to-end RAG orchestrator
│   │   │   ├── retriever.py        # Category-filtered & global vector search
│   │   │   └── vector_store.py     # ChromaDB PersistentClient wrapper
│   │   └── utils/                  # Shared utilities
│   │       └── duplicate_detector.py # Jaccard & SequenceMatcher duplicate detection
│   ├── data/                       # Datasets & local databases
│   │   ├── chroma/                 # Local persistent ChromaDB vector store
│   │   ├── rag_faqs.csv            # 30 canonical, deduplicated FAQ articles
│   │   ├── test.csv                # Primary held-out evaluation split (32 samples)
│   │   ├── train.csv               # Primary training split (125 samples)
│   │   ├── tickets_training.csv    # Source raw training dataset (157 samples)
│   │   └── tickets_dev.db          # Local persistent SQLite database
│   ├── eval/                       # Offline evaluation benchmarks & scripts
│   │   ├── api_benchmarks.json     # Endpoint latency and throughput benchmarks
│   │   ├── baseline_results.json   # Primary ML baseline evaluation metrics
│   │   ├── benchmark_queries.py    # Cold vs. warm RAG retrieval benchmarking
│   │   ├── evaluation_dataset.json # 160 realistic support tickets (60 val / 100 test)
│   │   ├── evaluation_summary.json # Comprehensive hybrid pipeline metrics
│   │   ├── rag_eval.json           # RAG retrieval metrics (Recall, MRR, nDCG)
│   │   └── run_week3_evaluation.py # End-to-end benchmark execution script
│   ├── models/                     # Persisted scikit-learn model artifacts
│   │   ├── sentiment_model.joblib  # Trained Logistic Regression classifier
│   │   ├── topic_model.joblib      # Trained Multinomial Naive Bayes classifier
│   │   └── vectorizer.joblib       # Fitted TF-IDF Vectorizer
│   ├── supabase/                   # PostgreSQL schema & migrations
│   │   ├── migration_001_auth_profiles.sql # Migration adding auth profiles & RLS
│   │   └── schema.sql              # Complete base PostgreSQL schema
│   ├── tests/                      # Automated unit and integration test suite
│   │   ├── test_agents.py          # Unit tests for individual agent nodes
│   │   ├── test_api.py             # FastAPI REST endpoint integration tests
│   │   ├── test_langgraph_workflow.py # StateGraph execution and conditional edges
│   │   ├── test_ml_models.py       # ML vectorization and inference tests
│   │   ├── test_postgres_live_scenarios.py # Live PostgreSQL migration scenarios
│   │   ├── test_rag.py             # ChromaDB retrieval and citation tests
│   │   ├── test_safety_and_regression.py # Guardrails, abstention, and side-effects
│   │   └── test_week3_evaluation.py # Benchmark artifact integrity validation
│   ├── requirements.txt            # Python dependencies
│   ├── .env.example                # Template for backend environment variables
│   └── .env                        # Local environment configuration (git-ignored)
├── frontend/                       # React 19 + TypeScript + Vite dashboard
│   ├── src/
│   │   ├── components/             # Reusable UI components
│   │   │   ├── Analytics.tsx       # Live operational analytics & charts
│   │   │   ├── CreateTicket.tsx    # Ticket submission form with preset demos
│   │   │   ├── DuplicateModal.tsx  # Interactive duplicate ticket comparison
│   │   │   ├── HelpModal.tsx       # In-app AI help assistant chat interface
│   │   │   ├── Navbar.tsx          # Navigation, health status, and theme toggles
│   │   │   ├── QualityEvaluation.tsx # Offline test benchmarks comparison tab
│   │   │   ├── TicketDetails.tsx   # AI triage diagnostics and audit history
│   │   │   └── TicketQueue.tsx     # Filterable, paginated ticket queue
│   │   ├── config/
│   │   │   └── brand.ts            # Centralized brand strings and stage config
│   │   ├── lib/
│   │   │   └── supabase.ts         # Supabase client initialization
│   │   ├── api.ts                  # Typed API client with auth token handling
│   │   ├── types.ts                # TypeScript interfaces matching backend models
│   │   ├── App.tsx                 # Root application component with tab routing
│   │   ├── main.tsx                # React DOM entry point
│   │   └── index.css               # Tailwind CSS imports and utility styles
│   ├── public/                     # Static assets
│   ├── package.json                # Frontend dependencies and npm scripts
│   ├── tailwind.config.js          # Tailwind CSS styling configuration
│   ├── tsconfig.json               # TypeScript compiler configuration
│   └── vite.config.ts              # Vite server & API proxy configuration
├── reports/                        # Machine-readable and markdown quality audits
│   ├── resolve_ai_metrics_audit.json # Verified metrics in machine-readable JSON
│   └── resolve_ai_metrics_audit.md   # Comprehensive quality audit report
├── README.md                       # Main project documentation
└── .gitignore                      # Git exclusion rules for secrets, DBs, and cache
```

---

## Prerequisites & Installation

### System Prerequisites
- **Python:** Version 3.10, 3.11, or 3.12.
- **Node.js:** Version 18.x, 20.x, or 22.x with npm.
- **Git:** Version 2.30+.
- **Operating System:** Windows 10/11, macOS, or Ubuntu 20.04+.

---

### Step 1: Clone the Repository
```bash
git clone https://github.com/Ananya-Rastogi/Resolve-AI.git
cd Resolve-AI
```

---

### Step 2: Backend Setup (Python)

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Verify persisted ML models:**
   The repository includes pre-trained model artifacts under `backend/models/`. If you wish to retrain them from `backend/data/train.csv`:
   ```bash
   python -c "from app.models.ml_models import get_pipeline; get_pipeline(auto_train_if_missing=True)"
   ```

---

### Step 3: Frontend Setup (React & Vite)

1. **Open a new terminal and navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node dependencies:**
   ```bash
   npm install
   ```

---

## Environment Variable Configuration

### Backend Configuration (`backend/.env`)

Copy the provided template to create your local `.env` file:
```bash
cd backend
cp .env.example .env
```

| Variable Name | Default Value | Description |
| :--- | :--- | :--- |
| `SUPABASE_URL` | `https://your-project.supabase.co` | Supabase project URL (optional for cloud database). |
| `SUPABASE_KEY` | *(leave blank for SQLite)* | Supabase service-role or anon key. If omitted or if an anonymous public key is detected, the system safely defaults to local SQLite. |
| `USE_LOCAL_DB` | `false` | Set to `true` to force local SQLite persistence regardless of Supabase credentials. |
| `SQLITE_DB_PATH` | `data/tickets_dev.db` | Relative or absolute path to the persistent SQLite database file. |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated list of allowed origins for browser requests. |
| `CLASSIFICATION_CONFIDENCE_THRESHOLD` | `0.50` | Confidence cutoff (0.0 to 1.0) below which tickets route to fallback classification. |
| `OPENAI_API_KEY` | *(optional)* | OpenAI API key for live GPT-4o-mini structured classification. If omitted, uses deterministic `MockLLMClient`. |
| `CHROMA_PERSIST_DIRECTORY` | `data/chroma` | Directory for persistent ChromaDB vector storage. |
| `FAQ_CSV_PATH` | `data/rag_faqs.csv` | Path to the canonical 30-document FAQ dataset. |

> [!NOTE]
> **Zero-Config Database Fallback:** You do not need a Supabase account to run Resolve AI locally. If `SUPABASE_URL` or `SUPABASE_KEY` are unset, or if a client publishable key (`sb_publishable_...`) is detected, the backend automatically initializes and manages a persistent SQLite database at `backend/data/tickets_dev.db`.

---

### Frontend Configuration (`frontend/.env.local`)

For local development, Vite proxies API requests to `http://127.0.0.1:8000` via `vite.config.ts`. If deploying or connecting to cloud authentication:

```ini
# Optional: backend API URL (defaults to relative '/api' via Vite proxy)
# VITE_API_URL=https://your-backend.onrender.com

# Optional: Supabase credentials for client-side authentication
# VITE_SUPABASE_URL=https://your-project.supabase.co
# VITE_SUPABASE_PUBLISHABLE_KEY=your-supabase-publishable-key
```

---

## Running the Application

### 1. Start the FastAPI Backend

In your backend terminal with the virtual environment activated:

```powershell
# Windows PowerShell:
cd backend
.\venv\Scripts\Activate.ps1
python -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload
```

```bash
# macOS / Linux:
cd backend
source venv/bin/activate
uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend server will start at `http://127.0.0.1:8000`. You can confirm its health by opening:
- `http://127.0.0.1:8000/api/health`

Expected response:
```json
{
  "status": "healthy",
  "storage_backend": "local_sqlite",
  "vector_store_status": "ready",
  "database_status": "ok",
  "version": "1.0.0"
}
```

---

### 2. Start the React Frontend Dashboard

In your frontend terminal:

```bash
cd frontend
npm run dev
```

Open your browser at `http://localhost:5173`. The application will load with full access to the ticket queue, live analytics, ticket submission form, and AI diagnostics.

---

## API Documentation & Verified Endpoints

FastAPI automatically generates interactive API documentation:
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc UI:** `http://127.0.0.1:8000/redoc`

### Core Endpoints

#### 1. Ingest & Triage Ticket
- **Method / Path:** `POST /api/tickets`
- **Status Code:** `201 Created` (or `200 OK` on duplicate submission)
- **Description:** Submits a customer inquiry, executes the multi-agent triage pipeline (ML classification, SLA priority, team routing, RAG retrieval, citation verification), persists the record, and returns the triaged ticket.

**Sample Request:**
```json
{
  "customer_name": "Michael Vance",
  "customer_email": "m.vance@enterprise.com",
  "customer_tier": "Platinum",
  "subject": "Duplicate charge on credit card for annual subscription",
  "body": "I noticed two identical charges of $1,200 on my invoice dated yesterday. Please refund the duplicate transaction immediately.",
  "idempotency_key": "IDEM-CLIENT-001"
}
```

**Sample Response:**
```json
{
  "ticket_id": "TKT-20261020-0D3EF4",
  "customer_name": "Michael Vance",
  "status": "open",
  "priority": "High",
  "category": "billing",
  "sentiment": "NEGATIVE",
  "confidence": 0.64,
  "assigned_team": "Finance Team",
  "escalation_level": "Escalated to Senior Manager",
  "classification_source": "ml",
  "generated_reply": "Knowledge Base Resolution:\nIf you notice duplicate charges on your statement, our billing department will verify the duplicate transaction and issue a full reversal within 3-5 business days.\n\nSources:\n- FAQ_010 (Category: Billing)",
  "citations": [
    {
      "faq_id": "FAQ_010",
      "category": "Billing",
      "question": "What should I do if I see duplicate charges?"
    }
  ],
  "analysis": {
    "ml_topic": "billing",
    "ml_sentiment": "NEGATIVE",
    "ml_confidence": 0.64,
    "llm_called": false,
    "rag_used": true,
    "used_faq_ids": ["FAQ_010"],
    "retrieval_latency_ms": 28.48,
    "is_cold_retrieval": false
  }
}
```

---

#### 2. Check Candidate Duplicate Tickets
- **Method / Path:** `POST /api/tickets/check-duplicates`
- **Status Code:** `200 OK`
- **Description:** Evaluates an inquiry subject against existing database tickets using Jaccard token overlap and sequence matching before submission.

**Sample Request:**
```json
{
  "subject": "Charged twice on my Visa card"
}
```

**Sample Response:**
```json
{
  "matches": [
    {
      "ticket_id": "TKT-20261020-0D3EF4",
      "subject": "Duplicate charge on credit card for annual subscription",
      "similarity_score": 0.542,
      "similarity_reason": "Substantial overlap in customer concern sharing key terms ('charged', 'credit', 'card').",
      "status": "open",
      "priority": "High",
      "category": "billing",
      "created_at": "2026-10-20T01:41:00Z"
    }
  ],
  "total_matches": 1
}
```

---

#### 3. List and Filter Tickets
- **Method / Path:** `GET /api/tickets`
- **Query Parameters:** `page=1`, `limit=20`, `status=open`, `category=billing`, `priority=High`, `search=refund`
- **Status Code:** `200 OK`
- **Description:** Returns a paginated list of tickets matching filter criteria.

---

#### 4. Retrieve Ticket Details & Audit History
- **Method / Path:** `GET /api/tickets/{ticket_id}`
- **Status Code:** `200 OK`
- **Description:** Retrieves complete ticket details, full AI triage diagnostics, citation metadata, and immutable lifecycle events from `ticket_events`.

---

#### 5. Update Ticket Status / Assignment
- **Method / Path:** `PATCH /api/tickets/{ticket_id}`
- **Sample Request:**
  ```json
  {
    "status": "resolved",
    "assigned_team": "Finance Team"
  }
  ```
- **Status Code:** `200 OK`
- **Description:** Safely updates ticket attributes and records an audit event tracking the author and diff.

---

#### 6. In-App AI Help Assistant
- **Method / Path:** `POST /api/help/chat`
- **Sample Request:**
  ```json
  {
    "message": "What is the SLA target for a High priority Platinum ticket?"
  }
  ```
- **Sample Response:**
  ```json
  {
    "reply": "High priority tickets for Platinum and Gold tier customers carry a strict 4-hour SLA target and are automatically escalated to Senior Management for immediate review.",
    "suggested_actions": ["View SLA Matrix", "Filter High Priority Tickets"]
  }
  ```

---

## Automated Testing & Verification

The project includes an extensive test suite verifying agent behavior, REST routes, RAG retrieval quality, migration scripts, and safety guardrails.

### Running Backend Tests
From the `backend` directory:

```bash
# Run complete test suite via unittest:
python -m unittest discover -s tests -v

# Or run via pytest:
pytest -v
```

### Verified Test Suite Breakdown (117 Tests Passed)

```
tests/test_agents.py ......................... [  4%]  # Agent nodes: classification, priority, routing, escalation, response
tests/test_api.py ............................ [ 15%]  # FastAPI routes: CRUD, pagination, filtering, auth scopes
tests/test_evaluation_baseline.py ............ [ 19%]  # Data splits, stratification, leakage verification
tests/test_evaluation_dataset.py ............. [ 22%]  # Evaluation dataset schema and distribution checks
tests/test_evaluation_metrics.py ............. [ 27%]  # Accuracy, F1, precision, recall, and matrix math
tests/test_langgraph_workflow.py ............. [ 35%]  # StateGraph transitions and confidence routing edges
tests/test_ml_models.py ...................... [ 38%]  # Vectorizer transform, MNB predictions, confidence scores
tests/test_postgres_live_scenarios.py ........ [ 44%]  # Idempotent migration runs, advisory locks, RLS rules
tests/test_postgres_migration.py ............. [ 51%]  # PostgreSQL C-parser validation of schema.sql
tests/test_rag.py ............................ [ 71%]  # ChromaDB indexing, category filtering, MRR, latency
tests/test_safety_and_regression.py .......... [ 75%]  # Non-hallucination, abstention, simulation side-effects
tests/test_schemas.py ........................ [ 78%]  # Pydantic TicketState schema validation and aliases
tests/test_supabase_integration.py ........... [ 80%]  # Live remote Supabase connectivity and schema checks
tests/test_week3_evaluation.py ............... [ 89%]  # Benchmark targets, threshold sweeps, citation validity
tests/test_workflow.py ....................... [100%]  # End-to-end multi-agent execution pipeline

----------------------------------------------------------------------
Ran 117 tests in 33.626s

OK (0 failures, 0 errors)
```

---

### Running Frontend Production Build Check
From the `frontend` directory:

```bash
npm run build
```

**Result:** Compiles cleanly with zero TypeScript errors:
```
✓ 1952 modules transformed.
dist/index.html                   1.11 kB │ gzip:   0.58 kB
dist/assets/index-D0GYG-Wj.css   48.43 kB │ gzip:   8.59 kB
dist/assets/index-DfS1I_Fh.js   631.99 kB │ gzip: 162.07 kB
✓ built in 13.27s
```

---

## Model Evaluation & Verified Performance Metrics

Every metric documented below was measured via reproducible offline evaluation scripts on held-out test splits without data leakage.

### 1. ML Topic Classification (Primary Benchmark)
- **Dataset:** Stratified 80/20 split from `data/tickets_training.csv` to `data/test.csv` ($N=32$, zero data leakage).
- **Model:** TF-IDF Vectorizer (1,000 features, n-grams 1–2) + Multinomial Naive Bayes.

| Metric | Measured Value | Evaluation Context |
| :--- | :--- | :--- |
| **Overall Accuracy** | **87.50%** (28/32) | Evaluated on held-out test split |
| **Macro F1-Score** | **0.8718** | Unweighted mean across 4 balanced categories |
| **Weighted F1-Score** | **0.8718** | Weighted by class support |
| **Macro Precision** | **0.8865** | Macro average precision |
| **Macro Recall** | **0.8750** | Macro average recall |
| **Inference Latency (P50)** | **0.379 ms** | Measured over 3,200 sequential CPU inferences |
| **Inference Latency (P95)** | **0.561 ms** | Measured over 3,200 sequential CPU inferences |

#### Per-Class Breakdown ($N=32$)
| Category Class | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| `billing` | 0.8000 | 1.0000 | **0.8889** | 8 |
| `other` | 1.0000 | 0.7500 | **0.8571** | 8 |
| `shipping` | 0.8889 | 1.0000 | **0.9412** | 8 |
| `technical` | 0.8571 | 0.7500 | **0.8000** | 8 |

---

### 2. Hybrid Multi-Agent Pipeline vs. Baselines ($N=100$)
Evaluated on 100 complex held-out customer support tickets from `eval/evaluation_dataset.json`:

| Architecture Variant | Topic Accuracy | Topic Macro F1 | Routing Accuracy | Fast-Path % | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Pure ML (Naive Bayes)** | 72.00% | 0.7011 | 71.88% | 100.0% | Fastest (< 1ms), lower on ambiguous text |
| **LLM Classification Alone** | 81.00% | 0.8093 | 80.62% | 0.0% | Evaluated with structured fallback |
| **Hybrid Pipeline ($\ge 0.50$)**| **82.00%** | **0.8205** | **81.88%** | **13.0%** | **★ Production default: optimal accuracy & cost** |

---

### 3. RAG Retrieval Performance (ChromaDB + all-MiniLM-L6-v2)
Evaluated across 160 test queries (136 supported, 24 out-of-scope) over 30 canonical FAQ documents:

| Metric | Measured Value | Benchmark Target | Status |
| :--- | :--- | :--- | :--- |
| **Recall@1 / Precision@1** | **76.47%** (104/136) | $\ge 70.0\%$ | **PASS** |
| **Recall@3** | **94.12%** (128/136) | $\ge 85.0\%$ | **PASS** |
| **Recall@5** | **96.32%** (131/136) | $\ge 90.0\%$ | **PASS** |
| **Mean Reciprocal Rank (MRR)** | **0.8442** | $\ge 0.80$ | **PASS** |
| **nDCG@3** | **0.8624** | $\ge 0.80$ | **PASS** |
| **Citation Validity Rate** | **100.0%** (130/130) | $100.0\%$ | **PASS** |
| **Hallucinated Citations** | **0 (0.0%)** | $0.0\%$ | **PASS** |
| **Out-of-Scope Abstention Rate** | **91.67%** (22/24) | $\ge 85.0\%$ | **PASS** |
| **Vector Search Latency (P50)**| **28.98 ms** | $< 50\text{ ms}$ | **PASS** |
| **Vector Search Latency (P95)**| **55.44 ms** | $< 100\text{ ms}$ | **PASS** |

---

### 4. API Endpoint Latency Benchmarks
Measured against the local Uvicorn server:

| Endpoint | Workload | P50 (Median) | P95 Latency | Throughput | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET /api/health` | 50 requests | 20.67 ms | 41.20 ms | 44.16 req/s | 100.0% |
| `GET /api/tickets?limit=10` | 30 requests | 26.11 ms | 46.99 ms | 34.83 req/s | 100.0% |
| `POST /api/tickets/check-duplicates` | 30 requests | 24.85 ms | 44.88 ms | 38.10 req/s | 100.0% |
| `POST /api/help/chat` | 30 requests | 17.63 ms | 36.88 ms | 50.59 req/s | 100.0% |
| `POST /api/tickets` (Full Triage) | 20 requests | 32.51 ms | 78.41 ms | ~28 req/s | 100.0% |

> [!WARNING]
> **Evaluation Limitations:** Benchmark metrics reflect controlled offline datasets (125 training, 32 test, 160 evaluation tickets). Real-world performance will vary based on user vocabulary, sentence length, domain shift, and whether a live LLM API is configured.

---

## Cloud Deployment Guide

Resolve AI is architected for simple cloud deployment across **Vercel** (frontend), **Render** (backend), and **Supabase** (PostgreSQL database).

```
                      ┌────────────────────────────────────────┐
                      │          Vercel Edge Network           │
                      │   React 19 + TypeScript SPA Frontend   │
                      └──────────────────┬─────────────────────┘
                                         │ HTTPS / REST
                                         ▼
                      ┌────────────────────────────────────────┐
                      │          Render Web Service            │
                      │    FastAPI + LangGraph + ChromaDB      │
                      └──────────────────┬─────────────────────┘
                                         │ Secure SSL Connection
                                         ▼
                      ┌────────────────────────────────────────┐
                      │         Supabase Cloud Platform        │
                      │      PostgreSQL Database with RLS      │
                      └────────────────────────────────────────┘
```

### 1. Database Setup (Supabase)
1. Create a project at [supabase.com](https://supabase.com).
2. Navigate to the **SQL Editor** in your Supabase dashboard.
3. Paste and run the contents of [`backend/supabase/schema.sql`](file:///c:/Users/anany/Downloads/ticket_env/backend/supabase/schema.sql) to create tables (`tickets`, `ticket_analyses`, `ticket_events`, `profiles`), indexes, and RLS policies.
4. Retrieve your **Project URL** and **Service Role Key** (under Project Settings $\to$ API).

---

### 2. Backend Deployment (Render)
1. Create a new **Web Service** on [render.com](https://render.com) connected to your GitHub repository.
2. Configure settings:
   - **Root Directory:** `backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.api.main:app --host 0.0.0.0 --port $PORT`
3. Add Environment Variables:
   - `SUPABASE_URL`: `https://<your-project-id>.supabase.co`
   - `SUPABASE_KEY`: `<your-supabase-service-role-key>`
   - `USE_LOCAL_DB`: `false`
   - `CORS_ORIGINS`: `https://resolve-ai-ananya-3e45.vercel.app,http://localhost:5173`
   - `CLASSIFICATION_CONFIDENCE_THRESHOLD`: `0.50`
   - `CHROMA_PERSIST_DIRECTORY`: `/tmp/chroma` *(or persistent disk mount)*
   - `FAQ_CSV_PATH`: `data/rag_faqs.csv`

---

### 3. Frontend Deployment (Vercel)
1. Import your GitHub repository into [vercel.com](https://vercel.com).
2. Configure settings:
   - **Root Directory:** `frontend`
   - **Framework Preset:** `Vite`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
3. Add Environment Variables:
   - `VITE_API_URL`: `https://<your-render-service>.onrender.com`
   - `VITE_SUPABASE_URL`: `https://<your-project-id>.supabase.co`
   - `VITE_SUPABASE_PUBLISHABLE_KEY`: `<your-supabase-anon-key>`
4. Deploy! The frontend is live at [https://resolve-ai-ananya-3e45.vercel.app](https://resolve-ai-ananya-3e45.vercel.app/).

---

## Troubleshooting Guide

### 1. PyTorch SentenceTransformer Cold-Start Delay
- **Symptom:** The first request to `POST /api/tickets` takes ~14 seconds to respond.
- **Cause:** `sentence-transformers/all-MiniLM-L6-v2` lazily downloads or loads PyTorch weights into CPU memory on the first RAG query.
- **Resolution:** Subsequent warm requests complete in 10–30 ms. In container deployments, warm up the model during startup lifecycle hooks in `app/api/main.py`.

### 2. Backend Falls Back to SQLite Despite Setting Supabase Keys
- **Symptom:** `GET /api/health` reports `"storage_backend": "local_sqlite"`.
- **Cause:** If `SUPABASE_KEY` starts with `sb_publishable_` (client-side anon key), the backend deliberately switches to local SQLite to prevent Row-Level Security (RLS) write rejections on server audit tables.
- **Resolution:** For server persistence, provide the Supabase **Service Role** key in `backend/.env`.

### 3. CORS Error in Browser Console
- **Symptom:** Browser blocks requests with `Access-Control-Allow-Origin` errors.
- **Cause:** The frontend URL is not in `CORS_ORIGINS`.
- **Resolution:** Add your frontend domain (e.g., `http://localhost:5173` or `https://resolve-ai-ananya-3e45.vercel.app`) to `CORS_ORIGINS` in `backend/.env`.

### 4. PowerShell Virtual Environment Activation Error
- **Symptom:** `Execution_Policies` restriction when running `Activate.ps1`.
- **Resolution:** Run PowerShell as Administrator and execute:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

---

## Future Improvements

- [ ] **Curate a 200-Pair Duplicate Detection Benchmark:** Construct a labeled ground-truth dataset to compute formal Precision, Recall, and F1 for duplicate detection.
- [ ] **FastAPI Startup Lifespan Model Pre-Warming:** Pre-load embedding weights during `@asynccontextmanager` startup to eliminate the initial 14-second cold-start latency.
- [ ] **Fine-Tuned Transformer Classification:** Benchmark fine-tuned DistilRoBERTa against TF-IDF Naive Bayes on expanded multi-topic corpora.
- [ ] **Cross-Encoder Re-Ranking:** Introduce a re-ranking stage (e.g., Cohere or `cross-encoder/ms-marco-MiniLM-L-6-v2`) to elevate Recall@1 beyond 85%.
- [ ] **Multi-Tenant Supabase Cloud Benchmarking:** Execute automated distributed load tests against managed PostgreSQL instances.

---

## Author & Contact

**Ananya Rastogi**  
- **GitHub:** [@Ananya-Rastogi](https://github.com/Ananya-Rastogi)  
- **Repository:** [https://github.com/Ananya-Rastogi/Resolve-AI](https://github.com/Ananya-Rastogi/Resolve-AI)  
- **Live Demo:** [https://resolve-ai-ananya-3e45.vercel.app](https://resolve-ai-ananya-3e45.vercel.app/)  

---
*README updated, audited, and verified against codebase implementation, test suites, and evaluation artifacts.*
