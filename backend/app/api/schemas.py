"""
Pydantic API request and response schemas for FastAPI backend.
"""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class HealthResponse(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: str
    storage_backend: str
    vector_store_status: str
    database_status: str
    version: str = "1.0.0"


class TicketCreateRequest(BaseModel):
    subject: str = Field(..., min_length=3, max_length=5000, description="Customer issue description or inquiry")
    customer_name: Optional[str] = Field(default="Anonymous Customer", max_length=255)
    customer_id: Optional[str] = Field(default=None, max_length=128)
    email: Optional[str] = Field(default=None, max_length=255)
    tier: Literal["Platinum", "Gold", "Silver", "Bronze"] = Field(default="Bronze")
    idempotency_key: Optional[str] = Field(default=None, max_length=128)

    @field_validator("subject")
    @classmethod
    def validate_subject(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Issue description cannot be blank.")
        return stripped


class TicketUpdateRequest(BaseModel):
    status: Optional[Literal["open", "in_progress", "resolved", "escalated"]] = None
    assigned_team: Optional[
        Literal[
            "Finance Team",
            "Logistics Team",
            "Tech Support",
            "General Support",
            "Billing Support",
            "Shipping Support",
            "Technical Support",
        ]
    ] = None
    priority: Optional[Literal["High", "Medium", "Low"]] = None
    escalation_level: Optional[str] = None
    actor: Optional[str] = Field(default="support_agent", max_length=128)


class TicketAnalysisSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ml_topic: Optional[str] = None
    ml_sentiment: Optional[str] = None
    ml_confidence: Optional[float] = None
    topic_confidence: Optional[float] = None
    sentiment_confidence: Optional[float] = None
    llm_called: bool = False
    llm_succeeded: bool = False
    fallback_occurred: bool = False
    llm_urgency: Optional[str] = None
    extracted_order_id: Optional[str] = None
    extracted_product: Optional[str] = None
    extracted_deadline: Optional[str] = None
    rag_query: Optional[str] = None
    rag_used: bool = False
    retrieved_faq_ids: List[Any] = Field(default_factory=list)
    used_faq_ids: List[Any] = Field(default_factory=list)
    retrieval_count: int = 0
    retrieval_latency_ms: Optional[float] = None
    embedding_query_ms: Optional[float] = None
    vector_search_ms: Optional[float] = None
    total_retrieval_ms: Optional[float] = None
    is_cold_retrieval: bool = False
    rag_error: Optional[str] = None


class TicketEventSchema(BaseModel):
    id: Optional[int] = None
    ticket_id: str
    event_type: str
    actor: str = "system"
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: str


class TicketResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ticket_id: str
    user_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_id: Optional[str] = None
    email: Optional[str] = None
    tier: str = "Bronze"
    subject: str
    status: str = "open"
    priority: str = "Medium"
    category: Optional[str] = None
    sentiment: Optional[str] = None
    confidence: Optional[float] = None
    assigned_team: Optional[str] = None
    escalation_level: str = "Not Escalated"
    classification_source: Optional[str] = None
    generated_reply: Optional[str] = None
    created_at: str
    updated_at: str


class UserProfileResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str = "agent"
    theme: str = "system"
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=255)
    avatar_url: Optional[str] = None
    theme: Optional[Literal["light", "dark", "system"]] = None
    preferences: Optional[Dict[str, Any]] = None


class AdminRoleUpdateRequest(BaseModel):
    role: Literal["admin", "manager", "agent"]


class TicketDetailResponse(TicketResponse):
    analysis: Optional[TicketAnalysisSchema] = None
    events: List[TicketEventSchema] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    retrieved_sources: List[Dict[str, Any]] = Field(default_factory=list)


class TicketListResponse(BaseModel):
    items: List[TicketResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class LiveMetrics(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    escalated_tickets: int
    high_priority_tickets: int
    category_distribution: Dict[str, int]
    priority_distribution: Dict[str, int]
    sentiment_distribution: Dict[str, int]
    team_distribution: Dict[str, int]
    storage_backend: str


class AnalyticsResponse(BaseModel):
    timestamp: str
    live_metrics: LiveMetrics
    offline_evaluation_benchmark: Optional[Dict[str, Any]] = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1, max_length=2000)


class HelpChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    current_page: Optional[str] = None
    history: Optional[List[ChatMessage]] = Field(default_factory=list)


class HelpChatResponse(BaseModel):
    reply: str
    suggested_actions: Optional[List[Dict[str, str]]] = Field(default_factory=list)


class DuplicateTicketMatch(BaseModel):
    ticket_id: str
    subject: str
    similarity_score: float
    similarity_reason: str
    status: str
    priority: str
    category: Optional[str] = None
    created_at: Optional[str] = None


class DuplicateCheckRequest(BaseModel):
    subject: str = Field(..., min_length=3, max_length=1000)
    exclude_ticket_id: Optional[str] = None


class DuplicateCheckResponse(BaseModel):
    matches: List[DuplicateTicketMatch]
    total_matches: int
