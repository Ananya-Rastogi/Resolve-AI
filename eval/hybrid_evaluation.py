"""
Hybrid Evaluation Infrastructure (Week 1 preparation).
Provides simulation and metrics tracking for hybrid ML + LLM routing
(distribution of ML vs LLM, fallback rates, and cost estimation).
"""
import time
from typing import Any, Dict, List, Optional
import pandas as pd

from app.models.schemas import TicketState
from app.models.ml_models import get_pipeline
from app.agents.llm_client import BaseLLMClient, MockLLMClient


def simulate_hybrid_routing(
    df: pd.DataFrame,
    threshold: float = 0.70,
    llm_client: Optional[BaseLLMClient] = None,
    cost_per_llm_call: float = 0.0005,  # Estimated input/output cost for gpt-4o-mini
) -> Dict[str, Any]:
    """
    Simulate the hybrid routing pipeline over a dataset to analyze routing trade-offs,
    percentage handled by ML vs LLM, fallback rate, and estimated costs.
    """
    pipeline = get_pipeline()
    client = llm_client or MockLLMClient()

    total_tickets = len(df)
    ml_handled = 0
    llm_routed = 0
    llm_succeeded = 0
    fallback_count = 0

    latencies_ml: List[float] = []
    latencies_llm: List[float] = []

    for _, row in df.iterrows():
        text = str(row["text"])

        # ML Prediction & Confidence
        t0 = time.perf_counter()
        topic, t_conf = pipeline.predict_topic_with_confidence(text)
        sentiment, s_conf = pipeline.predict_sentiment_with_confidence(text)
        t1 = time.perf_counter()
        latencies_ml.append((t1 - t0) * 1000.0)

        ml_conf = min(t_conf, s_conf)

        if ml_conf >= threshold:
            ml_handled += 1
        else:
            llm_routed += 1
            t2 = time.perf_counter()
            try:
                _ = client.classify_ticket(text)
                llm_succeeded += 1
            except Exception:
                fallback_count += 1
            t3 = time.perf_counter()
            latencies_llm.append((t3 - t2) * 1000.0)

    ml_pct = (ml_handled / total_tickets * 100.0) if total_tickets else 0.0
    llm_pct = (llm_routed / total_tickets * 100.0) if total_tickets else 0.0
    fallback_rate = (fallback_count / llm_routed * 100.0) if llm_routed else 0.0
    total_cost = llm_routed * cost_per_llm_call

    return {
        "total_tickets": total_tickets,
        "confidence_threshold": threshold,
        "ml_handled_count": ml_handled,
        "ml_handled_percentage": round(ml_pct, 2),
        "llm_routed_count": llm_routed,
        "llm_routed_percentage": round(llm_pct, 2),
        "llm_succeeded_count": llm_succeeded,
        "fallback_count": fallback_count,
        "fallback_rate_percentage": round(fallback_rate, 2),
        "estimated_llm_cost_usd": round(total_cost, 4),
        "avg_ml_latency_ms": round(sum(latencies_ml) / len(latencies_ml), 3) if latencies_ml else 0.0,
        "avg_llm_latency_ms": round(sum(latencies_llm) / len(latencies_llm), 3) if latencies_llm else 0.0,
    }
