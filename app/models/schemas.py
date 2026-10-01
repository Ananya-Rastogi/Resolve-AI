"""
Data models and schemas for customer support ticket state management and LLM outputs.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CustomerTier(str, Enum):
    """Customer loyalty / account tiers."""
    PLATINUM = "Platinum"
    GOLD = "Gold"
    SILVER = "Silver"
    BRONZE = "Bronze"


class TicketPriority(str, Enum):
    """Calculated ticket priority levels."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TicketSentiment(str, Enum):
    """Detected customer sentiment."""
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"


class TicketTopic(str, Enum):
    """Predicted ticket issue categories."""
    BILLING = "billing"
    SHIPPING = "shipping"
    TECHNICAL = "technical"
    OTHER = "other"


class LLMClassificationOutput(BaseModel):
    """
    Structured Pydantic schema for LLM classification output.
    Strictly constrains topic and sentiment while extracting auxiliary entities.
    """
    model_config = ConfigDict(extra="ignore")

    topic: Literal["billing", "shipping", "technical", "other"] = Field(
        ..., description="Ticket topic category"
    )
    sentiment: Literal["POSITIVE", "NEGATIVE"] = Field(
        ..., description="Customer sentiment"
    )
    urgency: Literal["low", "medium", "high", "critical"] = Field(
        default="medium", description="Urgency assessment"
    )
    extracted_order_id: Optional[str] = Field(
        default=None, description="Extracted order or tracking ID if present"
    )
    extracted_product: Optional[str] = Field(
        default=None, description="Extracted product or service name if present"
    )
    extracted_deadline: Optional[str] = Field(
        default=None, description="Extracted deadline or time constraint if present"
    )


class TicketState(BaseModel):
    """
    Typed ticket state tracking information across the agent pipeline.
    
    Supports both Pydantic attribute access (state.topic) and dictionary-like
    access (state['topic'], state.get('topic')) for backward compatibility.
    """
    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        extra="allow",
        validate_assignment=True,
    )

    # Customer Information
    customer_name: Optional[str] = Field(default=None, description="Name of the customer submitting the ticket")
    customer_id: Optional[str] = Field(default=None, description="Unique customer account identifier")
    email: Optional[str] = Field(default=None, alias="customer_email", description="Customer email address")
    tier: CustomerTier = Field(
        default=CustomerTier.BRONZE,
        alias="customer_tier",
        description="Customer account tier"
    )

    # Ticket Information
    subject: str = Field(..., alias="issue_description", description="Issue description or subject")
    ticket_id: Optional[str] = Field(default=None, alias="tracking_id", description="Unique tracking identifier (TKT-...)")
    created_at: Optional[datetime] = Field(default=None, description="Ticket creation timestamp")

    # Classification & AI Pipeline Fields
    topic: Optional[str] = Field(default=None, description="Predicted / finalized topic category")
    sentiment: Optional[str] = Field(default=None, description="Detected / finalized customer sentiment")
    priority: Optional[str] = Field(default=None, description="Calculated priority level (High, Medium, Low)")
    routed_to: Optional[str] = Field(default=None, alias="routing_destination", description="Assigned support team")
    escalation: Optional[str] = Field(default=None, alias="escalation_status", description="Escalation outcome")
    final_response: Optional[str] = Field(default=None, alias="generated_response", description="Customer response message")

    # ML & Hybrid Classification Tracking (Week 1)
    topic_confidence: Optional[float] = Field(default=None, description="ML probability for predicted topic")
    sentiment_confidence: Optional[float] = Field(default=None, description="ML probability for predicted sentiment")
    ml_confidence: Optional[float] = Field(default=None, description="Overall ML confidence (min of topic and sentiment)")
    confidence: Optional[float] = Field(default=None, description="Confidence score associated with finalized classification")
    classification_source: Optional[Literal["ml", "llm", "ml_fallback"]] = Field(
        default=None, description="Source of final classification: 'ml', 'llm', or 'ml_fallback'"
    )
    ml_topic: Optional[str] = Field(default=None, description="Initial topic predicted by scikit-learn ML")
    ml_sentiment: Optional[str] = Field(default=None, description="Initial sentiment predicted by scikit-learn ML")
    final_topic: Optional[str] = Field(default=None, description="Explicit final topic recorded for tracking")
    final_sentiment: Optional[str] = Field(default=None, description="Explicit final sentiment recorded for tracking")

    # LLM Structured Output Entities
    llm_urgency: Optional[str] = Field(default=None, description="Urgency assessed by LLM")
    extracted_order_id: Optional[str] = Field(default=None, description="Order ID extracted by LLM")
    extracted_product: Optional[str] = Field(default=None, description="Product extracted by LLM")
    extracted_deadline: Optional[str] = Field(default=None, description="Deadline extracted by LLM")

    # Pipeline Diagnostics
    llm_called: bool = Field(default=False, description="Whether LLM node was invoked")
    llm_succeeded: bool = Field(default=False, description="Whether LLM call succeeded")
    fallback_occurred: bool = Field(default=False, description="Whether fallback to ML occurred after LLM failure")

    # RAG Pipeline Fields (Week 2)
    rag_query: Optional[str] = Field(default=None, description="Query string used for vector search")
    rag_used: bool = Field(default=False, description="Whether RAG retrieval was executed and utilized")
    retrieved_context: Optional[str] = Field(default=None, description="Concatenated retrieved FAQ content formatted for LLM")
    retrieved_sources: list[dict[str, Any]] = Field(default_factory=list, description="List of retrieved source citations (faq_id, category, score)")
    used_sources: list[dict[str, Any]] = Field(default_factory=list, description="List of sources actually used in the response")
    retrieval_scores: list[float] = Field(default_factory=list, description="Similarity/relevance scores for retrieved documents")
    retrieval_metadata: list[dict[str, Any]] = Field(default_factory=list, description="Full metadata dicts for retrieved documents")
    retrieval_count: int = Field(default=0, description="Number of FAQ documents retrieved")
    retrieval_latency_ms: Optional[float] = Field(default=None, description="Retrieval latency in milliseconds")
    embedding_query_ms: Optional[float] = Field(default=None, description="Query embedding latency in ms")
    vector_search_ms: Optional[float] = Field(default=None, description="Vector search latency in ms")
    total_retrieval_ms: Optional[float] = Field(default=None, description="Total retrieval latency in ms")
    is_cold_retrieval: bool = Field(default=False, description="Whether this retrieval incurred cold-start initialization")
    rag_error: Optional[str] = Field(default=None, description="Error message if RAG retrieval encountered a failure")

    @property
    def citations(self) -> list[dict[str, Any]]:
        """Alias property returning sources actually used in the final response."""
        return self.used_sources

    @citations.setter
    def citations(self, value: list[dict[str, Any]]) -> None:
        self.used_sources = value

    @field_validator("subject", mode="before")
    @classmethod
    def validate_subject_not_empty(cls, v: Any) -> str:
        if v is None or not str(v).strip():
            raise ValueError("Issue description / subject cannot be empty.")
        return str(v).strip()

    @field_validator("tier", mode="before")
    @classmethod
    def normalize_tier(cls, v: Any) -> Any:
        if isinstance(v, str):
            for member in CustomerTier:
                if member.value.lower() == v.strip().lower():
                    return member
        return v

    # Dictionary compatibility helpers for backward compatibility
    def __getitem__(self, item: str) -> Any:
        if hasattr(self, item):
            return getattr(self, item)
        fields_by_alias = {f.alias: name for name, f in self.__class__.model_fields.items() if f.alias}
        if item in fields_by_alias:
            return getattr(self, fields_by_alias[item])
        if self.__pydantic_extra__ and item in self.__pydantic_extra__:
            return self.__pydantic_extra__[item]
        raise KeyError(item)

    def __setitem__(self, key: str, value: Any) -> None:
        fields_by_alias = {f.alias: name for name, f in self.__class__.model_fields.items() if f.alias}
        target = fields_by_alias.get(key, key)
        if hasattr(self, target):
            setattr(self, target, value)
        else:
            if self.__pydantic_extra__ is None:
                self.__pydantic_extra__ = {}
            self.__pydantic_extra__[key] = value

    def get(self, item: str, default: Any = None) -> Any:
        try:
            val = self[item]
            return val if val is not None else default
        except (KeyError, AttributeError):
            return default

    def to_dict(self) -> dict[str, Any]:
        """Return state as a standard Python dictionary."""
        return self.model_dump(by_alias=False)
