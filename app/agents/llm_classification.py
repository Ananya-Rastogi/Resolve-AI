"""
LLM Classification Agent: Structured classification with retries and graceful fallback.
"""
import logging
from typing import Optional, Union
from app.models.schemas import TicketState, LLMClassificationOutput
from app.agents.llm_client import BaseLLMClient, get_llm_client, LLMError

logger = logging.getLogger("ticket_workflow")

MAX_LLM_RETRIES = 2


def llm_classification_agent(
    state: Union[TicketState, dict],
    client: Optional[BaseLLMClient] = None,
) -> TicketState:
    """
    Classify uncertain tickets using an LLM provider with structured output.
    Implements up to 2 retries on schema or network failure.
    Falls back gracefully to ML predictions if all retries are exhausted.
    """
    if isinstance(state, dict):
        state = TicketState(**state)

    llm = client or get_llm_client()
    state.llm_called = True

    attempts = 0
    last_error: Optional[Exception] = None

    while attempts <= MAX_LLM_RETRIES:
        attempts += 1
        try:
            logger.info(f"LLM Classification attempt {attempts}/{MAX_LLM_RETRIES + 1} for ticket {state.ticket_id}")
            output: LLMClassificationOutput = llm.classify_ticket(state.subject)

            # Enforce validation
            if not isinstance(output, LLMClassificationOutput):
                output = LLMClassificationOutput.model_validate(output)

            # Successful classification
            state.topic = output.topic
            state.sentiment = output.sentiment
            state.final_topic = output.topic
            state.final_sentiment = output.sentiment
            state.llm_urgency = output.urgency
            state.extracted_order_id = output.extracted_order_id
            state.extracted_product = output.extracted_product
            state.extracted_deadline = output.extracted_deadline
            state.classification_source = "llm"
            state.confidence = 1.0
            state.llm_succeeded = True
            state.fallback_occurred = False

            logger.info(
                f"LLM Classification succeeded [Ticket {state.ticket_id}]: "
                f"topic='{output.topic}', sentiment='{output.sentiment}', urgency='{output.urgency}'"
            )
            return state

        except Exception as e:
            last_error = e
            logger.warning(
                f"LLM classification attempt {attempts} failed for ticket {state.ticket_id}: {e}"
            )

    # All retries failed -> Fallback to ML predictions
    logger.error(
        f"All {MAX_LLM_RETRIES + 1} LLM attempts failed for ticket {state.ticket_id} "
        f"({last_error}). Falling back to ML predictions."
    )
    state.classification_source = "ml_fallback"
    state.llm_succeeded = False
    state.fallback_occurred = True

    # Revert to ML topic and sentiment
    state.topic = state.ml_topic
    state.sentiment = state.ml_sentiment
    state.final_topic = state.ml_topic
    state.final_sentiment = state.ml_sentiment
    state.confidence = state.ml_confidence

    return state
