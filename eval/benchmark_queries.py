"""
Benchmarking script measuring Cold vs Warm retrieval latencies across consecutive queries.
"""
import time
from app.rag.embeddings import reset_embedding_cache, get_embedding_model, get_model_load_time_ms
from app.rag.vector_store import reset_vector_store_cache
from app.models.schemas import TicketState, CustomerTier
from app.graph.workflow import run_ticket_workflow, set_rag_pipeline

def run_benchmark():
    # 1. Reset all global caches to simulate fresh cold start
    reset_embedding_cache()
    reset_vector_store_cache()
    set_rag_pipeline(None)

    queries = [
        ("I was charged twice for my order ORD-88421, please refund immediately.", "Alice Smith", CustomerTier.GOLD),
        ("How can I return something I bought?", "Bob Jones", CustomerTier.SILVER),
        ("My package hasn't arrived yet.", "Charlie Brown", CustomerTier.BRONZE),
        ("I can't log into my account, password reset link is expired.", "Dana Scully", CustomerTier.PLATINUM),
    ]

    print("==================================================")
    print("COLD VS WARM RAG RETRIEVAL BENCHMARK")
    print("==================================================")

    results = []
    for i, (q, name, tier) in enumerate(queries, 1):
        state = TicketState(subject=q, customer_name=name, tier=tier)
        res = run_ticket_workflow(state)

        retrieved_ids = [s.get("faq_id") for s in res.retrieved_sources]
        used_ids = [s.get("faq_id") for s in res.used_sources]

        is_cold = res.is_cold_retrieval
        status = "COLD START" if is_cold else "WARM INFERENCE"

        print(f"\n--- Query {i} [{status}] ---")
        print(f"Subject: {q[:50]}...")
        print(f"Total Retrieval Latency (total_retrieval_ms): {res.total_retrieval_ms:.2f} ms")
        print(f"Query Embedding Latency (embedding_query_ms): {res.embedding_query_ms:.2f} ms")
        print(f"Vector Search Latency (vector_search_ms): {res.vector_search_ms:.2f} ms")
        print(f"Is Cold Retrieval: {is_cold}")
        print(f"Retrieved Sources ({len(res.retrieved_sources)}): {retrieved_ids}")
        print(f"Sources Used (Citations) ({len(res.used_sources)}): {used_ids}")
        results.append(res)

    cold_lat = results[0].total_retrieval_ms
    warm1_lat = results[1].total_retrieval_ms
    warm2_lat = results[2].total_retrieval_ms
    warm3_lat = results[3].total_retrieval_ms
    avg_warm = (warm1_lat + warm2_lat + warm3_lat) / 3

    print("\n==================================================")
    print("SUMMARY RESULTS")
    print("==================================================")
    print(f"First Query (Cold-Start):  {cold_lat:.2f} ms")
    print(f"Second Query (Warm):       {warm1_lat:.2f} ms")
    print(f"Third Query (Warm):        {warm2_lat:.2f} ms")
    print(f"Fourth Query (Warm):       {warm3_lat:.2f} ms")
    print(f"Average Warm Latency:      {avg_warm:.2f} ms")
    print("==================================================")

if __name__ == "__main__":
    run_benchmark()
