"""
Response agent: Grounded customer response generation using retrieved FAQ context.
Adheres to Phase 11 & Phase 12 by utilizing RAG retrieval context and verifiable citations.
"""
import logging
import re
from typing import Any, Optional, Union
from app.agents.llm_client import BaseLLMClient, get_llm_client
from app.models.schemas import TicketState
from app.rag.prompts import (
    RAG_RESPONSE_SYSTEM_PROMPT,
    RAG_RESPONSE_USER_PROMPT,
    format_retrieved_context_prompt,
)

logger = logging.getLogger("ticket_workflow")


def extract_used_sources(
    response_text: str,
    retrieved_sources: list[dict[str, Any]],
    retrieval_metadata: Optional[list[dict[str, Any]]] = None,
) -> list[dict[str, Any]]:
    """
    Extract only the sources from retrieved_sources that were actually used in the response.
    
    Guarantees:
    - Never fabricates or infers citations that were not retrieved or referenced.
    - Preserves retrieved document citation details (faq_id, category, score).
    - Supports multiple citations if multiple sources are genuinely referenced.
    - Citation IDs strictly correspond to retrieved documents.
    - Returns an empty list if no retrieved sources were utilized.
    """
    if not response_text or not retrieved_sources:
        return []

    # Map normalized FAQ IDs to source citations
    retrieved_map: dict[str, dict[str, Any]] = {}
    for src in retrieved_sources:
        fid = str(src.get("faq_id", "")).strip().upper()
        if fid:
            retrieved_map[fid] = src

    used_faq_ids: set[str] = set()

    # 1. Search for explicitly cited FAQ IDs in the response text (e.g. FAQ_010, FAQ-010, FAQ 010)
    found_faq_patterns = re.findall(r"\bFAQ[-_ ]?\d+\b", response_text, re.IGNORECASE)
    for raw_id in found_faq_patterns:
        normalized_id = raw_id.upper().replace("-", "_").replace(" ", "_")
        if normalized_id in retrieved_map:
            used_faq_ids.add(normalized_id)

    # 2. If no explicit FAQ ID cited, check for distinctive answer content match from metadata
    if not used_faq_ids and retrieval_metadata:
        resp_clean = response_text.lower()
        for meta in retrieval_metadata:
            fid = str(meta.get("faq_id", "")).strip().upper()
            if fid not in retrieved_map:
                continue
            answer = str(meta.get("answer", "")).strip().lower()
            if len(answer) > 25 and answer in resp_clean:
                used_faq_ids.add(fid)

    # 3. Preserve the original retrieval order for used sources
    used_sources: list[dict[str, Any]] = [
        src for src in retrieved_sources
        if str(src.get("faq_id", "")).strip().upper() in used_faq_ids
    ]

    return used_sources


def response_agent(
    state: Union[TicketState, dict],
    client: Optional[BaseLLMClient] = None,
) -> TicketState:
    """
    Generate customer response grounded in retrieved FAQ knowledge.
    
    Inputs received from TicketState:
    - subject / ticket text
    - topic / classification
    - sentiment
    - priority
    - routed_to / routing
    - escalation
    - retrieved_context / retrieved FAQ knowledge
    """
    if isinstance(state, dict):
        state = TicketState(**state)

    llm = client or get_llm_client()

    # Determine knowledge section for prompt
    knowledge_section = state.retrieved_context
    if not knowledge_section or not knowledge_section.strip():
        if state.retrieved_sources:
            knowledge_section = format_retrieved_context_prompt(state.retrieval_metadata)
        else:
            knowledge_section = "VERIFIED KNOWLEDGE BASE CONTEXT:\nNo relevant verified FAQ articles were found in the knowledge base."

    user_prompt = RAG_RESPONSE_USER_PROMPT.format(
        customer_name=state.customer_name or "Valued Customer",
        customer_tier=state.tier or "Bronze",
        ticket_id=state.ticket_id or "Pending",
        topic=state.topic or "General",
        sentiment=state.sentiment or "Neutral",
        priority=state.priority or "Normal",
        routed_to=state.routed_to or "Support Desk",
        escalation=state.escalation or "Standard",
        ticket_text=state.subject,
        retrieved_knowledge_section=knowledge_section,
    )

    topic_title = str(state.topic).title() if state.topic else "General"
    tkt_id = state.ticket_id or "Pending"
    priority = state.priority or "Normal"
    routed_to = state.routed_to or "Support Desk"
    escalation = state.escalation or "No Escalation Required"

    header_block = (
        f"Dear Customer,\n\n"
        f"Your ticket {tkt_id} has been successfully processed.\n\n"
        f"Issue Category: {topic_title}\n"
        f"Priority Level: {priority}\n"
        f"Assigned Team: {routed_to}\n"
        f"Escalation Status: {escalation}\n\n"
    )

    try:
        response_text = llm.generate_response(
            system_prompt=RAG_RESPONSE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        body = response_text.strip()
        state.final_response = (
            f"{header_block}"
            f"{body}\n\n"
            f"Our team will get back to you shortly.\n\n"
            f"Thank you for your patience."
        )
        logger.info(f"Generated grounded response for ticket {state.ticket_id}")
    except Exception as e:
        logger.error(f"Response generation error: {e}. Falling back to safe template.")
        # Fallback response ensuring graceful failure
        if state.retrieved_sources:
            src = state.retrieved_sources[0]
            faq_id = src.get("faq_id", "FAQ")
            cat = src.get("category", "General")
            resolution_text = (
                f"Knowledge Base Resolution:\n"
                f"Based on article {faq_id} ({cat}), we are reviewing your inquiry.\n\n"
                f"Sources:\n- {faq_id} (Category: {cat})"
            )
        else:
            resolution_text = (
                "Verified documentation addressing your specific inquiry could not be found in our knowledge base. "
                "Our team will review your inquiry manually."
            )

        state.final_response = (
            f"{header_block}"
            f"{resolution_text}\n\n"
            f"Our team will get back to you shortly.\n\n"
            f"Thank you for your patience."
        )

    # Separate retrieved_sources from used_sources / citations
    state.used_sources = extract_used_sources(
        response_text=state.final_response,
        retrieved_sources=state.retrieved_sources,
        retrieval_metadata=state.retrieval_metadata,
    )

    return state
