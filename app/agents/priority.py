"""
Priority agent: Calculates ticket priority based on customer tier and sentiment.
"""
from typing import Union
from app.models.schemas import TicketState, TicketPriority


def priority_agent(state: Union[TicketState, dict]) -> TicketState:
    """
    Calculate priority score based on customer tier and sentiment.
    Score >= 6 -> High
    Score >= 3 -> Medium
    Else -> Low
    """
    if isinstance(state, dict):
        state = TicketState(**state)

    tier_score = {
        "Platinum": 4,
        "Gold": 3,
        "Silver": 2,
        "Bronze": 1,
    }

    tier_str = state.tier.value if hasattr(state.tier, "value") else str(state.tier)
    sentiment_str = state.sentiment.value if hasattr(state.sentiment, "value") else str(state.sentiment)

    sentiment_weight = 2 if sentiment_str == "NEGATIVE" else 1
    score = tier_score.get(tier_str, 1) * sentiment_weight

    if score >= 6:
        state.priority = TicketPriority.HIGH.value
    elif score >= 3:
        state.priority = TicketPriority.MEDIUM.value
    else:
        state.priority = TicketPriority.LOW.value

    return state
