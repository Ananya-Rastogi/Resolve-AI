"""
Resolve AI Assistant: In-app help chatbot engine.
Provides clear, accurate guidance on Resolve AI features, navigation, priority, and SLA rules.
Safely integrates with OpenAI when configured, or provides high-accuracy deterministic assistance.
"""
import logging
import os
import re
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger("help_chatbot")

KNOWLEDGE_TOPICS = [
    {
        "keywords": ["create ticket", "new ticket", "submit ticket", "add ticket", "make ticket", "open ticket"],
        "reply": "To create a support ticket, select 'Create Ticket' in the sidebar (or top right on Overview). Fill in the Customer Subject, Issue Description, Customer Email, and Tier (Bronze, Silver, Gold, or Platinum). Resolve AI will immediately analyze the category, sentiment, and priority upon submission.",
        "actions": [{"label": "Open Create Ticket", "view": "create"}],
    },
    {
        "keywords": ["priority", "high priority", "medium priority", "low priority", "sla", "deadline"],
        "reply": "Ticket priority is determined by customer tier, issue urgency, and sentiment:\n• High: Urgent inquiries and Gold/Platinum accounts (4-hour resolution target).\n• Medium: Standard inquiries requiring investigation (24-hour resolution target).\n• Low: Routine inquiries and informational requests (72-hour resolution target).\nSLA statuses are marked as 'On Track', 'Due Soon', 'Overdue', or 'Needs Review'.",
        "actions": [{"label": "View Tickets", "view": "queue"}],
    },
    {
        "keywords": ["category", "categories", "routing", "assigned team", "departments", "teams"],
        "reply": "Resolve AI classifies tickets into 4 primary categories and routes them to specialized teams:\n• Billing & Charges → Finance Team\n• Shipping & Delivery → Logistics Team\n• Technical Support → Tech Support\n• General Questions → General Support\nCritical issues for Gold and Platinum tiers are automatically escalated for senior review.",
        "actions": [{"label": "View Ticket Queue", "view": "queue"}],
    },
    {
        "keywords": ["ai analysis", "tone", "confidence", "classification", "sentiment", "copilot"],
        "reply": "The AI Analysis breaks down every ticket:\n• Ticket Category: Predicted topic (e.g. Billing, Technical).\n• Customer Tone: Detected sentiment (Positive or Negative/Frustrated).\n• Suggested Priority: SLA urgency based on customer tier.\n• Suggested Reply: A grounded answer drafted using verified FAQ documentation.\nAgents must always review and approve any reply before sending.",
        "actions": [{"label": "View Recent Tickets", "view": "queue"}],
    },
    {
        "keywords": ["duplicate", "similar ticket", "merge", "duplicate check"],
        "reply": "Resolve AI scans existing tickets in real time to detect similar issues. When viewing a ticket or composing a new one, potential matches are suggested along with a similarity score and explanation. You can review the matches, but tickets are never automatically merged or deleted.",
        "actions": [{"label": "View Queue", "view": "queue"}],
    },
    {
        "keywords": ["analytics", "reports", "export", "csv", "metrics", "chart"],
        "reply": "In the Analytics section, you can review live operational statistics: open vs. resolved ticket volume, category distribution, and priority ratios. You can also export the current ticket list to CSV for reporting and spreadsheet analysis.",
        "actions": [{"label": "View Analytics", "view": "analytics"}],
    },
    {
        "keywords": ["tutorial", "onboarding", "tour", "guide", "walkthrough", "help"],
        "reply": "You can launch or replay the interactive 7-step onboarding tutorial at any time. It walks through the Overview, Ticket Queue, Creation Form, AI Analysis, and Analytics.",
        "actions": [{"label": "Start Tutorial", "action": "start_tutorial"}],
    },
    {
        "keywords": ["find assigned", "my tickets", "filter tickets", "search tickets"],
        "reply": "In the Tickets view, use the Search bar to find tickets by keyword or ID, and use the filters to narrow by Status (Open, In Progress, Resolved, Escalated), Category, Priority, or Assigned Team.",
        "actions": [{"label": "Go to Tickets", "view": "queue"}],
    },
]


def generate_help_response(
    message: str,
    current_page: Optional[str] = None,
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Generate an accurate, helpful reply for user questions about Resolve AI.
    Uses OpenAI if OPENAI_API_KEY is configured; otherwise uses deterministic knowledge matching.
    """
    cleaned = (message or "").strip()
    if not cleaned:
        return {
            "reply": "Hello! How can I help you navigate or manage tickets in Resolve AI today?",
            "suggested_actions": [],
        }

    # Attempt OpenAI if configured
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1") + "/chat/completions"
            system_prompt = (
                "You are the Resolve AI Assistant, a friendly and concise in-app support copilot. "
                "Help customer support specialists use the Resolve AI application. "
                "The application features: "
                "1. Overview dashboard with live ticket metrics and urgent ticket section. "
                "2. Tickets queue with search, category/priority/team filters, and CSV export. "
                "3. Create Ticket with automatic multi-agent AI triage (ML + LLM classification, ChromaDB RAG, and sentiment analysis). "
                "4. Ticket Details with editable AI-suggested grounded replies, verified FAQ citations, SLA tracking, and duplicate ticket detection. "
                "5. Analytics with operational stats and offline evaluation benchmarks. "
                "6. Interactive 7-step onboarding tutorial. "
                f"The user is currently on the '{current_page or 'overview'}' page. "
                "Never fabricate private records, tickets, or user data. Be concise, polite, and practical."
            )
            messages = [{"role": "system", "content": system_prompt}]
            if history:
                for h in history[-4:]:
                    messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
            messages.append({"role": "user", "content": cleaned})

            resp = requests.post(
                url,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={"model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"), "messages": messages, "temperature": 0.3},
                timeout=8,
            )
            if resp.status_code == 200:
                data = resp.json()
                reply_text = data["choices"][0]["message"]["content"].strip()
                return {"reply": reply_text, "suggested_actions": []}
        except Exception as e:
            logger.warning(f"Help chatbot OpenAI call failed, falling back to knowledge base: {e}")

    # Deterministic knowledge base matching
    cleaned_lower = cleaned.lower()
    for topic in KNOWLEDGE_TOPICS:
        if any(kw in cleaned_lower for kw in topic["keywords"]):
            return {
                "reply": topic["reply"],
                "suggested_actions": topic.get("actions", []),
            }

    # Page-contextual fallback
    if current_page == "create":
        return {
            "reply": "You are currently on the Create Ticket page. Fill out the subject and customer issue details to trigger automatic category classification, priority calculation, and suggested response drafting.",
            "suggested_actions": [],
        }
    if current_page == "queue":
        return {
            "reply": "You are in the Ticket Queue. You can search tickets by ID or text, filter by status, priority, or team, and click any ticket to review its AI analysis and reply suggestion.",
            "suggested_actions": [{"label": "Create New Ticket", "view": "create"}],
        }
    if current_page == "analytics":
        return {
            "reply": "You are in the Analytics view. Here you can inspect live ticket volumes, category distributions, and SLA metrics. You can also export ticket records to CSV.",
            "suggested_actions": [],
        }

    return {
        "reply": (
            "I'm here to help you get the most out of Resolve AI. You can ask me how to create tickets, "
            "how priority and SLAs are calculated, how to filter tickets, or how AI-suggested responses work. "
            "You can also restart the onboarding tour anytime from the Help page."
        ),
        "suggested_actions": [
            {"label": "How does priority work?", "prompt": "How does ticket priority work?"},
            {"label": "How do I create a ticket?", "prompt": "How do I create a ticket?"},
        ],
    }
