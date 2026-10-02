"""
Utility functions for ticket handling.
"""
import uuid
from datetime import datetime


def generate_ticket_id() -> str:
    """Generate a unique ticket tracking ID in format TKT-YYYYMMDD-XXXXXX."""
    date = datetime.now().strftime("%Y%m%d")
    unique = str(uuid.uuid4())[:6].upper()
    return f"TKT-{date}-{unique}"
