"""
Escalation agent: Determines whether ticket requires management escalation.
"""
from typing import Union
from app.models.schemas import TicketState


def escalation_agent(state: Union[TicketState, dict]) -> TicketState:
    """
    Escalate high-priority tickets belonging to Platinum and Gold tier customers.
    """
    if isinstance(state, dict):
        state = TicketState(**state)

    tier_str = state.tier.value if hasattr(state.tier, "value") else str(state.tier)
    priority_str = state.priority.value if hasattr(state.priority, "value") else str(state.priority)

    if priority_str == "High" and tier_str in ["Platinum", "Gold"]:
        state.escalation = "Escalated to Senior Manager"
    else:
        state.escalation = "No Escalation Required"

    return state
