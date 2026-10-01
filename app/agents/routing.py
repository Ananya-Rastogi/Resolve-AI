"""
Routing agent: Directs tickets to appropriate department based on predicted topic.
"""
from typing import Union
from app.models.schemas import TicketState


ROUTING_MAP = {
    "billing": "Finance Team",
    "shipping": "Logistics Team",
    "technical": "Tech Support",
    "other": "General Support",
}


def routing_agent(state: Union[TicketState, dict]) -> TicketState:
    """
    Route ticket to the designated team according to its topic.
    """
    if isinstance(state, dict):
        state = TicketState(**state)

    topic_str = str(state.topic).lower() if state.topic else "other"
    state.routed_to = ROUTING_MAP.get(topic_str, "General Support")

    return state
