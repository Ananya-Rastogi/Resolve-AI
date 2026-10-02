"""
LangGraph Workflow Orchestration for Hybrid Multi-Agent Ticket Processing.
Implements StateGraph with ML-first classification and conditional routing to LLM.
"""
import logging
import os
from typing import Any, Dict, Literal, Optional, Union
from langgraph.graph import StateGraph, START, END

from app.models.schemas import TicketState
from app.agents.classification import classification_agent
from app.agents.llm_classification import llm_classification_agent
from app.agents.priority import priority_agent
from app.agents.routing import routing_agent
from app.agents.escalation import escalation_agent
from app.agents.response import response_agent

logger = logging.getLogger("ticket_workflow")

# In a 4-class MultinomialNB classifier, uniform probability is 0.25 and the max probability
# observed on training data is ~0.633 (median ~0.494). A threshold of 0.50 ensures tickets with strong
# probability (2x random baseline) stay on ML, while ambiguous ones route to the LLM.
DEFAULT_CONFIDENCE_THRESHOLD = 0.50


def get_confidence_threshold() -> float:
    """Retrieve the classification confidence threshold from environment or default."""
    try:
        return float(os.getenv("CLASSIFICATION_CONFIDENCE_THRESHOLD", str(DEFAULT_CONFIDENCE_THRESHOLD)))
    except (ValueError, TypeError):
        return DEFAULT_CONFIDENCE_THRESHOLD


def route_after_classification(state: TicketState) -> Literal["priority", "llm_classification"]:
    """
    Conditional edge router:
    If ML confidence >= threshold -> accept ML prediction and route directly to priority.
    If ML confidence < threshold  -> route to LLM classification for expert triage.
    """
    threshold = get_confidence_threshold()
    conf = state.ml_confidence if state.ml_confidence is not None else 0.0

    if conf >= threshold:
        logger.info(
            f"Confidence check [Ticket {state.ticket_id}]: High ML confidence ({conf:.3f} >= {threshold:.3f}) "
            f"-> routing directly to 'priority'"
        )
        return "priority"

    logger.info(
        f"Confidence check [Ticket {state.ticket_id}]: Low ML confidence ({conf:.3f} < {threshold:.3f}) "
        f"-> routing to 'llm_classification'"
    )
    return "llm_classification"


# Node wrapper functions ensuring TicketState instance handling
def ml_classification_node(state: TicketState) -> Dict[str, Any]:
    updated = classification_agent(state)
    return updated.to_dict()


def llm_classification_node(state: TicketState) -> Dict[str, Any]:
    updated = llm_classification_agent(state)
    return updated.to_dict()


def priority_node(state: TicketState) -> Dict[str, Any]:
    updated = priority_agent(state)
    return updated.to_dict()


def routing_node(state: TicketState) -> Dict[str, Any]:
    updated = routing_agent(state)
    return updated.to_dict()


def escalation_node(state: TicketState) -> Dict[str, Any]:
    updated = escalation_agent(state)
    return updated.to_dict()


_rag_pipeline = None


def get_rag_pipeline():
    """Retrieve or initialize the singleton RAG pipeline."""
    global _rag_pipeline
    if _rag_pipeline is None:
        from app.rag.pipeline import RAGPipeline
        _rag_pipeline = RAGPipeline()
    return _rag_pipeline


def set_rag_pipeline(pipeline):
    """Explicitly configure the singleton RAG pipeline (used by Streamlit / tests)."""
    global _rag_pipeline
    _rag_pipeline = pipeline


def rag_retrieval_node(state: TicketState) -> Dict[str, Any]:
    """Retrieve relevant FAQ documentation for the ticket issue."""
    pipeline = get_rag_pipeline()
    updated = pipeline.process_ticket(state)
    return updated.to_dict()


def response_node(state: TicketState) -> Dict[str, Any]:
    updated = response_agent(state)
    return updated.to_dict()


def create_ticket_graph() -> StateGraph:
    """Construct and configure the LangGraph StateGraph."""
    graph = StateGraph(TicketState)

    # Add Nodes
    graph.add_node("classification", ml_classification_node)
    graph.add_node("llm_classification", llm_classification_node)
    graph.add_node("priority", priority_node)
    graph.add_node("routing", routing_node)
    graph.add_node("escalation", escalation_node)
    graph.add_node("rag_retrieval", rag_retrieval_node)
    graph.add_node("response", response_node)

    # Edge: Start -> ML Classification
    graph.add_edge(START, "classification")

    # Conditional Edge: Classification -> Priority (High Conf) OR LLM Classification (Low Conf)
    graph.add_conditional_edges(
        "classification",
        route_after_classification,
        {
            "priority": "priority",
            "llm_classification": "llm_classification",
        },
    )

    # Edge: LLM Classification -> Priority
    graph.add_edge("llm_classification", "priority")

    # Downstream Linear Flow
    graph.add_edge("priority", "routing")
    graph.add_edge("routing", "escalation")
    graph.add_edge("escalation", "rag_retrieval")
    graph.add_edge("rag_retrieval", "response")
    graph.add_edge("response", END)

    return graph


# Global compiled workflow application
_compiled_app = None


def get_compiled_workflow():
    """Retrieve or build the compiled LangGraph application."""
    global _compiled_app
    if _compiled_app is None:
        graph = create_ticket_graph()
        _compiled_app = graph.compile()
    return _compiled_app


def run_ticket_workflow(
    initial_state: Union[TicketState, dict],
    compiled_app: Optional[Any] = None,
) -> TicketState:
    """
    Execute the hybrid multi-agent LangGraph ticket triage workflow.
    Returns the fully populated TicketState.
    """
    if isinstance(initial_state, dict):
        state_in = TicketState(**initial_state)
    else:
        state_in = initial_state.model_copy()

    app = compiled_app or get_compiled_workflow()
    result_dict = app.invoke(state_in)

    result_state = TicketState(**result_dict) if isinstance(result_dict, dict) else result_dict

    # Structured Ticket Audit Log
    logger.info(
        f"Ticket Triage Complete | ID: {result_state.ticket_id} | "
        f"Source: {result_state.classification_source} | "
        f"ML_Conf: {result_state.ml_confidence:.3f} | "
        f"Final_Topic: {result_state.topic} | "
        f"Final_Sentiment: {result_state.sentiment} | "
        f"LLM_Called: {result_state.llm_called} | "
        f"LLM_Succeeded: {result_state.llm_succeeded} | "
        f"Fallback_Occurred: {result_state.fallback_occurred}"
    )

    return result_state
