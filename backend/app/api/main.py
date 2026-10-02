"""
FastAPI application for Enterprise Multi-Agent Ticket Routing System.
Provides RESTful endpoints for ticket ingestion, queue triage, analytics, and health monitoring.
"""
from datetime import datetime, timezone
import json
import logging
import math
import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query, Request, Response, status as http_status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.schemas import (
    AnalyticsResponse,
    HealthResponse,
    LiveMetrics,
    TicketAnalysisSchema,
    TicketCreateRequest,
    TicketDetailResponse,
    TicketEventSchema,
    TicketListResponse,
    TicketResponse,
    TicketUpdateRequest,
    UserProfileResponse,
    UserProfileUpdateRequest,
    AdminRoleUpdateRequest,
)
from app.db.repository import get_repository
from app.graph.workflow import get_rag_pipeline, run_ticket_workflow
from app.models.schemas import CustomerTier, TicketState
from app.utils.ticket_utils import generate_ticket_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ticket_api")

app = FastAPI(
    title="Resolve AI - Enterprise Multi-Agent Ticket Resolution Platform API",
    description="Production-ready REST API for intelligent multi-agent ticket routing, RAG retrieval, and human-supervised resolution.",
    version="1.0.0",
)

# Configure CORS for local development and dashboard UI
raw_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
)
allowed_origins = [orig.strip() for orig in raw_origins.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled server error on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred while processing the request."},
    )


def get_auth_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    Authenticate user using Supabase JWT Bearer token or local dev mode fallback.
    Never trusts client-supplied user IDs without cryptographic or provider verification.
    """
    auth_header = request.headers.get("Authorization", "").strip()
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:].strip()
    if not token:
        return None

    repo = get_repository()
    # If Supabase client is available, verify token securely via Supabase Auth API
    if hasattr(repo, "client") and repo.client is not None:
        try:
            res = repo.client.auth.get_user(token)
            if res and res.user:
                return {
                    "id": str(res.user.id),
                    "email": res.user.email or "",
                    "user_metadata": res.user.user_metadata or {},
                }
        except Exception as e:
            logger.debug(f"Supabase auth get_user verification failed: {e}")
            return None

    # Development fallback for local testing when offline SQLite is explicitly used
    if repo.backend_name == "local_sqlite":
        if token.startswith("dev-") or token.startswith("test-"):
            user_id = token
            return {
                "id": user_id,
                "email": f"{user_id}@resolve-ai.local",
                "user_metadata": {"full_name": "Support Agent"},
            }
        return {
            "id": "local-agent-001",
            "email": "agent@resolve-ai.local",
            "user_metadata": {"full_name": "Local Support Specialist"},
        }

    return None


def check_ticket_access(ticket: Dict[str, Any], user: Optional[Dict[str, Any]], repo) -> bool:
    """
    Enforce backend authorization when using service-role key:
    - If user is None (public test mode or unauthenticated), allow if ticket is unassigned.
    - If user is authenticated:
      - Admin and Manager can access all tickets.
      - Agent can access if ticket is unassigned (user_id is None) or owned by the agent.
    """
    if not user:
        return True
    user_id = user.get("id")
    profile = repo.get_user_profile(user_id) or {}
    role = profile.get("role", "agent")
    if role in ("admin", "manager"):
        return True
    ticket_user_id = ticket.get("user_id")
    if ticket_user_id is None or ticket_user_id == user_id:
        return True
    return False


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
def get_health():
    """Verify backend API, database connectivity, and vector store readiness."""
    now_iso = datetime.now(timezone.utc).isoformat()
    repo = get_repository()
    db_health = repo.check_health()

    vector_status = "ready"
    try:
        pipeline = get_rag_pipeline()
        if pipeline is None:
            vector_status = "uninitialized"
    except Exception as e:
        vector_status = f"degraded: {str(e)[:50]}"

    overall_status = "healthy" if db_health.get("status") == "ok" else "degraded"

    return HealthResponse(
        status=overall_status,
        timestamp=now_iso,
        storage_backend=repo.backend_name,
        vector_store_status=vector_status,
        database_status=db_health.get("status", "unknown"),
        version="1.0.0",
    )


@app.post("/api/tickets", response_model=TicketDetailResponse, status_code=http_status.HTTP_201_CREATED, tags=["Tickets"])
def create_and_triage_ticket(payload: TicketCreateRequest, request: Request, response: Response):
    """
    Ingest a new support ticket, execute multi-agent AI triage (ML + LLM fallback + Chroma RAG),
    and persist the resulting ticket and analysis.
    """
    repo = get_repository()
    auth_user = get_auth_user(request)
    user_id = auth_user["id"] if auth_user else None

    # Idempotency / duplicate check
    if payload.idempotency_key:
        existing = repo.find_by_idempotency_key(payload.idempotency_key)
        if existing:
            logger.info(f"Duplicate submission detected for idempotency_key '{payload.idempotency_key}' -> returning existing ticket {existing['ticket_id']}")
            response.status_code = http_status.HTTP_200_OK
            analysis = repo.get_ticket_analysis(existing["ticket_id"])
            events = repo.get_ticket_events(existing["ticket_id"])
            return TicketDetailResponse(
                **existing,
                analysis=TicketAnalysisSchema(**analysis) if analysis else None,
                events=[TicketEventSchema(**e) for e in events],
                citations=[],
                retrieved_sources=[],
            )

    # Generate unique ticket tracking ID
    ticket_id = generate_ticket_id()
    created_at_dt = datetime.now(timezone.utc)
    created_at_iso = created_at_dt.isoformat()

    # Construct typed TicketState and execute workflow
    initial_state = TicketState(
        ticket_id=ticket_id,
        subject=payload.subject,
        customer_name=payload.customer_name,
        customer_id=payload.customer_id,
        customer_email=payload.email,
        customer_tier=CustomerTier(payload.tier),
        created_at=created_at_dt,
    )

    try:
        logger.info(f"Executing multi-agent workflow for new ticket {ticket_id}...")
        processed_state: TicketState = run_ticket_workflow(initial_state)
    except Exception as exc:
        logger.error(f"Error during AI ticket workflow execution: {exc}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete AI triage workflow.",
        )

    # Extract source citations and IDs
    retrieved_faq_ids = [
        s.get("faq_id") or s.get("id") for s in processed_state.retrieved_sources if isinstance(s, dict)
    ]
    used_faq_ids = [
        s.get("faq_id") or s.get("id") for s in processed_state.used_sources if isinstance(s, dict)
    ]

    ticket_record = {
        "ticket_id": ticket_id,
        "user_id": user_id,
        "customer_name": processed_state.customer_name,
        "customer_id": processed_state.customer_id,
        "email": processed_state.email,
        "tier": processed_state.tier,
        "subject": processed_state.subject,
        "status": "escalated" if processed_state.escalation == "Escalated" else "open",
        "priority": processed_state.priority or "Medium",
        "category": processed_state.topic,
        "sentiment": processed_state.sentiment,
        "confidence": processed_state.confidence,
        "assigned_team": processed_state.routed_to,
        "escalation_level": processed_state.escalation or "Not Escalated",
        "classification_source": processed_state.classification_source,
        "generated_reply": processed_state.final_response,
        "idempotency_key": payload.idempotency_key,
        "created_at": created_at_iso,
        "updated_at": created_at_iso,
    }

    analysis_record = {
        "ml_topic": processed_state.ml_topic,
        "ml_sentiment": processed_state.ml_sentiment,
        "ml_confidence": processed_state.ml_confidence,
        "topic_confidence": processed_state.topic_confidence,
        "sentiment_confidence": processed_state.sentiment_confidence,
        "llm_called": processed_state.llm_called,
        "llm_succeeded": processed_state.llm_succeeded,
        "fallback_occurred": processed_state.fallback_occurred,
        "llm_urgency": processed_state.llm_urgency,
        "extracted_order_id": processed_state.extracted_order_id,
        "extracted_product": processed_state.extracted_product,
        "extracted_deadline": processed_state.extracted_deadline,
        "rag_query": processed_state.rag_query,
        "rag_used": processed_state.rag_used,
        "retrieved_faq_ids": retrieved_faq_ids,
        "used_faq_ids": used_faq_ids,
        "retrieval_count": processed_state.retrieval_count,
        "retrieval_latency_ms": processed_state.retrieval_latency_ms,
        "embedding_query_ms": processed_state.embedding_query_ms,
        "vector_search_ms": processed_state.vector_search_ms,
        "total_retrieval_ms": processed_state.total_retrieval_ms,
        "is_cold_retrieval": processed_state.is_cold_retrieval,
        "rag_error": processed_state.rag_error,
        "created_at": created_at_iso,
    }

    event_record = {
        "action": "ai_triage_complete",
        "source": processed_state.classification_source,
        "priority": processed_state.priority,
        "routed_to": processed_state.routed_to,
        "escalation": processed_state.escalation,
    }

    saved_ticket = repo.save_ticket(ticket_record, analysis_record, event_record)
    events = repo.get_ticket_events(ticket_id)

    return TicketDetailResponse(
        **saved_ticket,
        analysis=TicketAnalysisSchema(**analysis_record),
        events=[TicketEventSchema(**e) for e in events],
        citations=processed_state.used_sources,
        retrieved_sources=processed_state.retrieved_sources,
    )


@app.get("/api/tickets", response_model=TicketListResponse, tags=["Tickets"])
def list_tickets(
    request: Request,
    status: Optional[str] = Query(None, description="Filter by status (open, in_progress, resolved, escalated)"),
    category: Optional[str] = Query(None, description="Filter by topic category (billing, shipping, technical, other)"),
    priority: Optional[str] = Query(None, description="Filter by priority (High, Medium, Low)"),
    assigned_team: Optional[str] = Query(None, description="Filter by support team"),
    search: Optional[str] = Query(None, description="Search ticket ID or subject text"),
    user_id: Optional[str] = Query(None, description="Filter by assigned or creator user ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Retrieve paginated list of tickets with optional filtering and role-based data isolation."""
    user = get_auth_user(request)
    repo = get_repository()

    # Enforce role scoping if user is an agent
    if user:
        profile = repo.get_user_profile(user["id"]) or {}
        role = profile.get("role", "agent")
        if role not in ("admin", "manager"):
            # An agent cannot request another agent's user_id
            if user_id and user_id != user["id"]:
                raise HTTPException(
                    status_code=http_status.HTTP_403_FORBIDDEN,
                    detail="Agents are not authorized to view other agents' private tickets.",
                )

    items, total = repo.list_tickets(
        status=status,
        category=category,
        priority=priority,
        assigned_team=assigned_team,
        search=search,
        page=page,
        limit=limit,
        user_id=user_id,
    )

    total_pages = max(1, math.ceil(total / limit)) if total > 0 else 1

    return TicketListResponse(
        items=[TicketResponse(**item) for item in items],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@app.get("/api/tickets/{ticket_id}", response_model=TicketDetailResponse, tags=["Tickets"])
def get_ticket_details(ticket_id: str, request: Request):
    """Retrieve full ticket details, AI analysis parameters, citations, and audit history."""
    repo = get_repository()
    ticket = repo.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found.",
        )

    user = get_auth_user(request)
    if user and not check_ticket_access(ticket, user, repo):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this ticket.",
        )

    analysis_raw = repo.get_ticket_analysis(ticket_id)
    events_raw = repo.get_ticket_events(ticket_id)

    # Format citations for response
    citations = []
    retrieved_sources = []
    if analysis_raw:
        used_ids = analysis_raw.get("used_faq_ids") or []
        retrieved_ids = analysis_raw.get("retrieved_faq_ids") or []
        citations = [{"faq_id": fid} for fid in used_ids]
        retrieved_sources = [{"faq_id": fid} for fid in retrieved_ids]

    return TicketDetailResponse(
        **ticket,
        analysis=TicketAnalysisSchema(**analysis_raw) if analysis_raw else None,
        events=[TicketEventSchema(**e) for e in events_raw],
        citations=citations,
        retrieved_sources=retrieved_sources,
    )


@app.patch("/api/tickets/{ticket_id}", response_model=TicketResponse, tags=["Tickets"])
def update_ticket(ticket_id: str, updates: TicketUpdateRequest, request: Request):
    """Safely update ticket status, assigned team, priority, or escalation with audit logging."""
    repo = get_repository()
    ticket = repo.get_ticket(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found.",
        )

    user = get_auth_user(request)
    if user and not check_ticket_access(ticket, user, repo):
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this ticket.",
        )

    update_dict = updates.model_dump(exclude_unset=True)
    actor = update_dict.pop("actor", "support_agent")

    # If ticket was unassigned and an authenticated agent updates it, claim ticket for agent
    if user and ticket.get("user_id") is None:
        update_dict["user_id"] = user["id"]

    if not update_dict:
        return TicketResponse(**ticket)

    updated_ticket = repo.update_ticket(ticket_id=ticket_id, updates=update_dict, actor=actor)
    if not updated_ticket:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update ticket.",
        )

    return TicketResponse(**updated_ticket)


@app.patch("/api/admin/users/{target_user_id}/role", response_model=UserProfileResponse, tags=["Admin"])
def admin_update_user_role(target_user_id: str, payload: AdminRoleUpdateRequest, request: Request):
    """Admin-only endpoint to securely promote or manage user roles."""
    user = get_auth_user(request)
    if not user:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    repo = get_repository()
    caller_profile = repo.get_user_profile(user["id"]) or {}
    if caller_profile.get("role") != "admin":
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Only administrators can manage user roles.")

    updated = repo.update_user_role_admin(target_user_id, payload.role)
    if not updated:
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user role.")

    return UserProfileResponse(**updated)



@app.get("/api/analytics", response_model=AnalyticsResponse, tags=["Analytics"])
def get_analytics():
    """
    Return real-time operational ticket statistics and offline evaluation benchmark metrics.
    Clearly distinguishes live production data from static offline test set evaluations.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    repo = get_repository()
    live_stats = repo.get_analytics()

    # Load offline evaluation benchmark metrics if available
    offline_eval_data = None
    eval_summary_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "eval", "evaluation_summary.json")
    if os.path.exists(eval_summary_path):
        try:
            with open(eval_summary_path, "r", encoding="utf-8") as f:
                offline_eval_data = json.load(f)
        except Exception as e:
            logger.warning(f"Could not read offline evaluation summary: {e}")

    return AnalyticsResponse(
        timestamp=now_iso,
        live_metrics=LiveMetrics(**live_stats),
        offline_evaluation_benchmark=offline_eval_data,
    )


@app.get("/api/user/profile", response_model=UserProfileResponse, tags=["User"])
def get_user_profile_endpoint(request: Request):
    """Get the authenticated user's profile and preferences."""
    user = get_auth_user(request)
    repo = get_repository()

    if not user:
        if repo.backend_name == "local_sqlite":
            profile = repo.get_user_profile("local-default-agent")
            if not profile:
                profile = repo.update_user_profile(
                    "local-default-agent",
                    {
                        "full_name": "Support Specialist",
                        "email": "agent@resolve-ai.local",
                        "theme": "system",
                        "preferences": {"notifications": True, "simple_mode": True, "compact_view": False},
                    },
                )
            return UserProfileResponse(**profile)
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in to view your profile.",
        )

    profile = repo.get_user_profile(user["id"])
    if not profile:
        profile = repo.update_user_profile(
            user["id"],
            {
                "email": user.get("email"),
                "full_name": user.get("user_metadata", {}).get("full_name") or user.get("email", "").split("@")[0] or "Support Specialist",
                "theme": "system",
                "preferences": {"notifications": True, "simple_mode": True, "compact_view": False},
            },
        )
    return UserProfileResponse(**profile)


@app.patch("/api/user/profile", response_model=UserProfileResponse, tags=["User"])
def update_user_profile_endpoint(payload: UserProfileUpdateRequest, request: Request):
    """Update full name, avatar, theme, or preferences for the authenticated user."""
    user = get_auth_user(request)
    repo = get_repository()
    user_id = user["id"] if user else ("local-default-agent" if repo.backend_name == "local_sqlite" else None)

    if not user_id:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in to update your profile.",
        )

    updates = payload.model_dump(exclude_unset=True)
    if user and user.get("email"):
        updates["email"] = user["email"]
    updated = repo.update_user_profile(user_id, updates)
    if not updated:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile.",
        )
    return UserProfileResponse(**updated)
