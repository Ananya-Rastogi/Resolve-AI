"""
Test the 5 specific user validation queries through the end-to-end LangGraph RAG pipeline.
"""
from app.graph.workflow import run_ticket_workflow
from app.models.schemas import TicketState

test_cases = [
    "I was charged twice for my order.",
    "How can I return something I bought?",
    "My package hasn't arrived yet.",
    "I can't log into my account.",
    "How do I fix a loading error?",
]

print("=" * 80)
print("       END-TO-END RAG VALIDATION ON USER-SPECIFIED TEST QUERIES")
print("=" * 80)

for i, q in enumerate(test_cases, 1):
    state = TicketState(subject=q)
    res = run_ticket_workflow(state)

    print(f"Test Case {i}: \"{q}\"")
    print(f"  Ticket ID:           {res.ticket_id}")
    print(f"  Predicted Topic:     {res.topic}")
    print(f"  Priority & Team:     {res.priority} -> {res.routed_to}")
    print(f"  RAG Retrieval Used:  {res.rag_used}")
    print(f"  Retrieval Count:     {res.retrieval_count} documents")
    print(f"  Retrieval Latency:   {res.retrieval_latency_ms:.2f} ms")

    print("  Retrieved Sources:")
    for src in res.retrieved_sources:
        print(f"    - {src.get('faq_id')} | Category: {src.get('category')} | Score: {src.get('score'):.4f}")

    print("  Grounded Response Body:")
    for line in res.final_response.splitlines():
        if "Knowledge Base Resolution:" in line or "Sources:" in line or line.startswith("- FAQ_"):
            print(f"    {line}")
    print("-" * 80)

print("=" * 80)
