"""
ML Classification Agent: Initial scikit-learn classification with confidence extraction.
"""
import logging
from typing import Union
from app.models.schemas import TicketState
from app.models.ml_models import detect_topic_with_confidence, detect_sentiment_with_confidence
from app.utils.ticket_utils import generate_ticket_id

logger = logging.getLogger("ticket_workflow")


def classification_agent(state: Union[TicketState, dict]) -> TicketState:
    """
    Classify the ticket subject using classical scikit-learn models (TF-IDF + NB / LogReg),
    extract probability confidences, and assign a unique ticket ID.
    """
    if isinstance(state, dict):
        state = TicketState(**state)

    if not state.ticket_id:
        state.ticket_id = generate_ticket_id()

    subject_text = state.subject or ""

    # Obtain predictions and class probabilities from persisted scikit-learn models
    topic, topic_conf = detect_topic_with_confidence(subject_text)
    sentiment, sent_conf = detect_sentiment_with_confidence(subject_text)

    # Calculate overall ML confidence as conservative minimum
    overall_conf = float(min(topic_conf, sent_conf))

    # Record ML baseline predictions and confidences
    state.ml_topic = topic
    state.ml_sentiment = sentiment
    state.topic_confidence = float(topic_conf)
    state.sentiment_confidence = float(sent_conf)
    state.ml_confidence = overall_conf

    # By default, populate topic/sentiment with ML predictions
    state.topic = topic
    state.sentiment = sentiment
    state.final_topic = topic
    state.final_sentiment = sentiment
    state.confidence = overall_conf
    state.classification_source = "ml"

    logger.info(
        f"ML Classification [Ticket {state.ticket_id}]: "
        f"topic='{topic}' (conf={topic_conf:.3f}), "
        f"sentiment='{sentiment}' (conf={sent_conf:.3f}), "
        f"overall_ml_confidence={overall_conf:.3f}"
    )

    return state
