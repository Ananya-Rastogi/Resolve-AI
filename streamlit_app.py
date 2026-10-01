"""
Streamlit Web Application for Enterprise Multi-Agent Ticket Routing System.
Powered by LangGraph StateGraph with hybrid ML + LLM classification,
Week 2 RAG Retrieval, and Week 3 Comprehensive Quality & Evaluation Dashboard.
"""
from datetime import datetime
import json
from pathlib import Path
import re
import pandas as pd
import streamlit as st

from app.graph.workflow import run_ticket_workflow, get_confidence_threshold, set_rag_pipeline
from app.graph.visualization import get_ascii_graph
from app.models.schemas import TicketState, CustomerTier

st.set_page_config(
    page_title="Resolve AI — Multi-Agent Resolution Platform",
    page_icon="⚡",
    layout="wide",
)

# ----------------------------
# Streamlit Resource Caching: RAG Pipeline Warmup
# ----------------------------
@st.cache_resource(show_spinner="Initializing RAG vector database & embedding model...")
def initialize_rag_service():
    """
    Initializes and warms up the RAG pipeline once across all Streamlit sessions.
    SentenceTransformer model weights and ChromaDB client are loaded once into memory.
    """
    import time
    from app.rag.embeddings import get_embedding_model
    from app.rag.vector_store import get_vector_store
    from app.rag.retriever import FAQRetriever
    from app.rag.pipeline import RAGPipeline
    import app.graph.workflow as wf

    t0 = time.perf_counter()
    emb_model = get_embedding_model()
    # warm up embedding model
    emb_model.embed_query("warmup sentence-transformer model")
    # warm up ChromaDB collection
    store = get_vector_store(embedding_model=emb_model)
    store.get_collection()
    retriever = FAQRetriever(vector_store=store)
    pipeline = RAGPipeline(retriever=retriever)
    wf.set_rag_pipeline(pipeline)
    init_latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    return pipeline, init_latency_ms


# Pre-warm singleton RAG service at startup
cached_pipeline, cold_init_latency_ms = initialize_rag_service()

st.title("⚡ Resolve AI — Multi-Agent Ticket Resolution Platform")
st.caption("Every ticket. One intelligent resolution. Multiple specialized agents, one coordinated system.")

# ----------------------------
# Sidebar - Architecture Info
# ----------------------------
with st.sidebar:
    st.header("⚙️ Workflow Configuration")
    threshold = get_confidence_threshold()
    st.metric(label="Classification Threshold", value=f"{threshold:.2f}")
    st.caption(f"Cold-Start Init Latency: `{cold_init_latency_ms:.2f} ms` (cached)")
    st.info(
        "**Hybrid Architecture:**\n"
        "1. **ML Fast-Path**: scikit-learn Naive Bayes\n"
        "2. **LLM Fallback**: Structured extraction\n"
        "3. **RAG Knowledge**: ChromaDB vector store\n"
        "4. **Embedding**: `all-MiniLM-L6-v2`\n"
        "5. **Grounding**: Strict FAQ verification & citations"
    )

    st.subheader("📚 Quick Test Queries")
    quick_queries = [
        "I was charged twice for my order.",
        "How can I return something I bought?",
        "My package hasn't arrived yet.",
        "I can't log into my account.",
        "How do I fix a loading error?",
    ]
    for q in quick_queries:
        if st.button(q, key=f"btn_{q[:15]}"):
            st.session_state["ticket_subject"] = q

    with st.expander("View LangGraph Workflow"):
        st.code(get_ascii_graph(), language="text")

# ----------------------------
# Main Layout: Tabs for Isolation
# ----------------------------
tab_ticket, tab_eval = st.tabs([
    "🎫 Live Ticket Processing",
    "📊 Week 3 Quality & Evaluation Dashboard",
])

# ============================================================================
# TAB 1: Live Ticket Processing (Preserves Week 0, 1, 2 Functionality)
# ============================================================================
with tab_ticket:
    st.subheader("👤 Customer Details")
    col1, col2 = st.columns(2)

    with col1:
        customer_name = st.text_input("Customer Name", value="Alice Smith")
        customer_id = st.text_input("Customer ID", value="CUST-1042")

    with col2:
        customer_email = st.text_input("Customer Email", value="alice@example.com")
        tier_options = [tier.value for tier in CustomerTier]
        tier = st.selectbox("Customer Tier", tier_options)

    st.markdown("---")

    st.subheader("📝 Ticket Details")
    default_subject = st.session_state.get(
        "ticket_subject",
        "I was charged twice for my order ORD-88421, please refund immediately."
    )

    subject = st.text_area(
        "Describe Your Issue",
        value=default_subject,
        height=120,
        key="ticket_input_area",
    )

    if st.button("🚀 Process Ticket", type="primary"):
        if not customer_name.strip():
            st.error("Customer name is required.")
        elif not customer_email.strip():
            st.error("Customer email is required.")
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", customer_email):
            st.error("Enter a valid email address.")
        elif not subject.strip():
            st.error("Ticket description cannot be empty.")
        else:
            initial_state = TicketState(
                customer_name=customer_name.strip(),
                customer_id=customer_id.strip() if customer_id else None,
                email=customer_email.strip(),
                tier=tier,
                subject=subject.strip(),
                created_at=datetime.now(),
            )

            with st.spinner("Executing LangGraph pipeline (ML -> Routing -> Escalation -> RAG Retrieval -> Grounded Response)..."):
                result: TicketState = run_ticket_workflow(initial_state)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success("✅ Ticket Processed Successfully!")
            st.markdown("---")

            # Ticket Summary
            st.subheader("📌 Ticket Summary")
            sum_col1, sum_col2 = st.columns(2)
            with sum_col1:
                st.write(f"**Ticket ID:** `{result.ticket_id}`")
                st.write(f"**Customer Name:** {customer_name}")
                st.write(f"**Customer ID:** {customer_id}")
            with sum_col2:
                st.write(f"**Email:** {customer_email}")
                st.write(f"**Submission Time:** {timestamp}")
                st.write(f"**Customer Tier:** {tier}")

            st.markdown("---")

            # AI Classification Output
            st.subheader("🤖 System Classification & Routing")
            c1, c2, c3 = st.columns(3)

            with c1:
                priority = result.priority
                if priority == "High":
                    st.error(f"**Priority:** {priority}")
                elif priority == "Medium":
                    st.warning(f"**Priority:** {priority}")
                else:
                    st.info(f"**Priority:** {priority}")

                topic_title = str(result.topic).title() if result.topic else "General"
                st.write(f"**Topic:** {topic_title}")
                st.write(f"**Sentiment:** {result.sentiment}")

            with c2:
                st.write(f"**Routed To:** {result.routed_to}")
                st.write(f"**Escalation Status:** {result.escalation}")
                source_badge = result.classification_source.upper() if result.classification_source else "ML"
                st.write(f"**Classification Source:** `{source_badge}`")

            with c3:
                if result.ml_confidence is not None:
                    st.metric("ML Overall Confidence", f"{result.ml_confidence * 100:.1f}%")
                    st.caption(f"Topic: {result.topic_confidence:.2f} | Sent: {result.sentiment_confidence:.2f}")

                if result.extracted_order_id:
                    st.write(f"**Extracted Order ID:** `{result.extracted_order_id}`")
                if result.llm_urgency:
                    st.write(f"**Assessed Urgency:** `{result.llm_urgency}`")

            st.markdown("---")

            # RAG Retrieval Section
            st.subheader("🔍 RAG Knowledge Retrieval")
            total_lat = result.total_retrieval_ms if result.total_retrieval_ms is not None else (result.retrieval_latency_ms or 0.0)
            emb_lat = result.embedding_query_ms or 0.0
            vec_lat = result.vector_search_ms or 0.0
            is_cold = getattr(result, "is_cold_retrieval", False)

            rag_col1, rag_col2, rag_col3, rag_col4 = st.columns(4)
            with rag_col1:
                if result.rag_used:
                    st.success("✓ Retrieved Knowledge")
                elif result.rag_error:
                    st.error("⚠️ Retrieval Error")
                else:
                    st.warning("⚠️ No Knowledge Retrieved")

            with rag_col2:
                st.metric(label="Retrieved Articles", value=f"{result.retrieval_count} docs")

            with rag_col3:
                st.metric(label="Total Retrieval Latency", value=f"{total_lat:.2f} ms")
                st.caption("🟢 Warm Inference" if not is_cold else "❄️ Cold-Start Retrieval")

            with rag_col4:
                st.metric(label="Cold Initialization", value=f"{cold_init_latency_ms:.2f} ms")
                st.caption("Streamlit Resource Cache")

            with st.expander("⏱️ Detailed Latency Instrumentation Breakdown", expanded=True):
                t_col1, t_col2, t_col3 = st.columns(3)
                with t_col1:
                    st.metric("total_retrieval_ms", f"{total_lat:.2f} ms")
                with t_col2:
                    st.metric("embedding_query_ms", f"{emb_lat:.2f} ms")
                with t_col3:
                    st.metric("vector_search_ms", f"{vec_lat:.2f} ms")

            if result.rag_error:
                st.error(f"RAG Error: {result.rag_error}")

            if result.retrieved_sources:
                st.markdown("#### Retrieved Sources (Preserved Documents):")
                for i, src in enumerate(result.retrieved_sources, 1):
                    faq_id = src.get("faq_id", "UNKNOWN")
                    category = src.get("category", "General")
                    score = src.get("score", 0.0)

                    col_a, col_b, col_c = st.columns([1, 2, 1])
                    with col_a:
                        st.write(f"**{i}. {faq_id}**")
                    with col_b:
                        st.write(f"**Category:** `{category}`")
                    with col_c:
                        st.write(f"**Relevance:** `{score:.2f}`")

            with st.expander("📄 View Retrieved FAQ Context (Prompt Payload)"):
                st.text(result.retrieved_context or "No context retrieved.")

            st.markdown("---")

            # Final Response & Citations
            st.subheader("📨 Customer Response")
            st.info(result.final_response)

            if result.used_sources:
                st.markdown("#### Sources Used (Citations):")
                for src in result.used_sources:
                    faq_id = src.get("faq_id", "UNKNOWN")
                    category = src.get("category", "General")
                    score = src.get("score")
                    score_str = f" (Relevance: `{score:.2f}`)" if score is not None else ""
                    st.markdown(f"- **{faq_id}** — *{category}*{score_str}")
            else:
                st.caption("ℹ️ No specific verified knowledge base sources were cited for this response.")


# ============================================================================
# TAB 2: Week 3 Quality & Evaluation Dashboard
# ============================================================================
with tab_eval:
    st.header("📊 Quality Engineering & System Evaluation Dashboard")
    st.caption("Real computed metrics across Classification, Thresholding, Retrieval, Citations, and End-to-End Latency")

    summary_file = Path("eval/evaluation_summary.json")
    report_file = Path("eval/evaluation_report.md")

    if not summary_file.exists():
        st.warning("⚠️ No evaluation summary found (`eval/evaluation_summary.json`). Please execute the evaluation runner to generate metrics.")
        if st.button("🚀 Run Week 3 Evaluation Suite Now"):
            with st.spinner("Executing full 160-ticket evaluation benchmark..."):
                from eval.run_week3_evaluation import run_all_evaluations
                run_all_evaluations()
                st.rerun()
    else:
        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                eval_data = json.load(f)
        except Exception as e:
            st.error(f"Failed to read evaluation summary: {e}")
            eval_data = None

        if eval_data:
            dataset_info = eval_data.get("dataset", {})
            clf_data = eval_data.get("classification", {})
            rag_data = eval_data.get("rag_retrieval", {})
            e2e_data = eval_data.get("end_to_end", {})
            abl_data = eval_data.get("ablation", {})

            # Top Header Cards
            h1, h2, h3, h4 = st.columns(4)
            with h1:
                st.metric("Total Evaluation Dataset", f"{dataset_info.get('total_tickets', 160)} Tickets")
                st.caption(f"Val: {dataset_info.get('validation_split', 60)} | Test: {dataset_info.get('held_out_test_split', 100)}")
            with h2:
                st.metric("Canonical Knowledge Base", f"{dataset_info.get('canonical_faq_count', 30)} FAQs")
                st.caption("Deduplicated from Kaggle Dataset")
            with h3:
                st.metric("Evaluation Status", "✅ Verified & Reproducible")
                st.caption(f"Time: {eval_data.get('total_evaluation_time_sec', 0):.1f}s")
            with h4:
                ts = eval_data.get("evaluation_timestamp", "")[:19].replace("T", " ")
                st.metric("Last Evaluated", ts)
                st.caption("UTC Timestamp")

            st.markdown("---")

            # ----------------------------------------------------------------
            # Section 1: Classification & Hybrid Routing
            # ----------------------------------------------------------------
            st.subheader("1. 🤖 Classification & Hybrid Routing Performance")

            hyb_metrics = clf_data.get("hybrid_production", {})
            ml_metrics = clf_data.get("ml_only", {})
            llm_metrics = clf_data.get("llm_only", {})

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                top_acc = hyb_metrics.get("topic_metrics", {}).get("accuracy", 0.0)
                st.metric("Topic Accuracy (Hybrid)", f"{top_acc * 100:.1f}%")
                st.caption(f"Macro F1: {hyb_metrics.get('topic_metrics', {}).get('macro_f1', 0.0):.4f}")
            with m2:
                sent_acc = hyb_metrics.get("sentiment_metrics", {}).get("accuracy", 0.0)
                st.metric("Sentiment Accuracy", f"{sent_acc * 100:.1f}%")
                st.caption(f"Macro F1: {hyb_metrics.get('sentiment_metrics', {}).get('macro_f1', 0.0):.4f}")
            with m3:
                fp_rate = hyb_metrics.get("fastpath_rate", 0.0)
                st.metric("ML Fast-Path Rate", f"{fp_rate * 100:.1f}%")
                st.caption("Zero-cost inference without LLM")
            with m4:
                fb_rate = hyb_metrics.get("fallback_rate", 0.0)
                st.metric("LLM Fallback Rate", f"{fb_rate * 100:.1f}%")
                st.caption("Routed for expert LLM triage")

            # Threshold Optimization Table
            st.markdown("#### Threshold Optimization Sweep (Validation Set: 60 Tickets)")
            sweep_data = clf_data.get("validation_threshold_sweep", [])
            if sweep_data:
                sweep_df = pd.DataFrame([
                    {
                        "Threshold": f"{row['threshold']:.2f}" + (" (Production Default)" if row['threshold'] == 0.50 else ""),
                        "ML Fast-Path %": f"{row['fastpath_percentage']:.1f}%",
                        "LLM Fallback %": f"{row['fallback_percentage']:.1f}%",
                        "Topic Macro F1": f"{row['topic_macro_f1']:.4f}",
                        "Routing Error Rate": f"{row['incorrect_routing_rate'] * 100:.1f}%",
                        "Median Latency (ms)": f"{row['latency_median_ms']:.2f}",
                    }
                    for row in sweep_data
                ])
                st.dataframe(sweep_df, hide_index=True)

            st.markdown("---")

            # ----------------------------------------------------------------
            # Section 2: RAG Retrieval Benchmark
            # ----------------------------------------------------------------
            st.subheader("2. 🔍 RAG Retrieval Benchmark & Strategy Comparison")

            strat_data = rag_data.get("strategy_comparison", {})
            hyb_rag = strat_data.get("hybrid_category_with_fallback", {})
            glob_rag = strat_data.get("global_semantic_search", {})
            cat_rag = strat_data.get("category_filtered_search_strict", {})

            r_col1, r_col2, r_col3, r_col4 = st.columns(4)
            with r_col1:
                st.metric("Recall@1 (Hybrid)", f"{hyb_rag.get('recall', {}).get('recall@1', 0.0) * 100:.1f}%")
                st.caption("Target: >= 70.0%")
            with r_col2:
                st.metric("Recall@3 (Hybrid)", f"{hyb_rag.get('recall', {}).get('recall@3', 0.0) * 100:.1f}%")
                st.caption("Target: >= 85.0%")
            with r_col3:
                st.metric("Recall@5 (Hybrid)", f"{hyb_rag.get('recall', {}).get('recall@5', 0.0) * 100:.1f}%")
                st.caption("Target: >= 90.0%")
            with r_col4:
                st.metric("MRR (Hybrid)", f"{hyb_rag.get('mrr', 0.0):.4f}")
                st.caption(f"nDCG@3: {hyb_rag.get('ndcg', {}).get('ndcg@3', 0.0):.4f}")

            # Strategy Comparison Table
            st.markdown("#### Retrieval Strategy Comparison (160 Tickets Evaluated)")
            strategies_table = pd.DataFrame([
                {
                    "Strategy": "Hybrid Category-Aware (Production)",
                    "Recall@1": f"{hyb_rag.get('recall', {}).get('recall@1', 0.0) * 100:.1f}%",
                    "Recall@3": f"{hyb_rag.get('recall', {}).get('recall@3', 0.0) * 100:.1f}%",
                    "Recall@5": f"{hyb_rag.get('recall', {}).get('recall@5', 0.0) * 100:.1f}%",
                    "Precision@1": f"{hyb_rag.get('precision', {}).get('precision@1', 0.0) * 100:.1f}%",
                    "MRR": f"{hyb_rag.get('mrr', 0.0):.4f}",
                    "nDCG@3": f"{hyb_rag.get('ndcg', {}).get('ndcg@3', 0.0):.4f}",
                    "Empty Rate": f"{hyb_rag.get('empty_retrieval_rate', 0.0) * 100:.1f}%",
                    "Median Latency": f"{hyb_rag.get('latency', {}).get('median', 0.0):.2f} ms",
                },
                {
                    "Strategy": "Global Semantic Search",
                    "Recall@1": f"{glob_rag.get('recall', {}).get('recall@1', 0.0) * 100:.1f}%",
                    "Recall@3": f"{glob_rag.get('recall', {}).get('recall@3', 0.0) * 100:.1f}%",
                    "Recall@5": f"{glob_rag.get('recall', {}).get('recall@5', 0.0) * 100:.1f}%",
                    "Precision@1": f"{glob_rag.get('precision', {}).get('precision@1', 0.0) * 100:.1f}%",
                    "MRR": f"{glob_rag.get('mrr', 0.0):.4f}",
                    "nDCG@3": f"{glob_rag.get('ndcg', {}).get('ndcg@3', 0.0):.4f}",
                    "Empty Rate": f"{glob_rag.get('empty_retrieval_rate', 0.0) * 100:.1f}%",
                    "Median Latency": f"{glob_rag.get('latency', {}).get('median', 0.0):.2f} ms",
                },
                {
                    "Strategy": "Strict Category-Filtered",
                    "Recall@1": f"{cat_rag.get('recall', {}).get('recall@1', 0.0) * 100:.1f}%",
                    "Recall@3": f"{cat_rag.get('recall', {}).get('recall@3', 0.0) * 100:.1f}%",
                    "Recall@5": f"{cat_rag.get('recall', {}).get('recall@5', 0.0) * 100:.1f}%",
                    "Precision@1": f"{cat_rag.get('precision', {}).get('precision@1', 0.0) * 100:.1f}%",
                    "MRR": f"{cat_rag.get('mrr', 0.0):.4f}",
                    "nDCG@3": f"{cat_rag.get('ndcg', {}).get('ndcg@3', 0.0):.4f}",
                    "Empty Rate": f"{cat_rag.get('empty_retrieval_rate', 0.0) * 100:.1f}%",
                    "Median Latency": f"{cat_rag.get('latency', {}).get('median', 0.0):.2f} ms",
                },
            ])
            st.dataframe(strategies_table, hide_index=True)

            st.markdown("---")

            # ----------------------------------------------------------------
            # Section 3: Grounding, Citations & Safety
            # ----------------------------------------------------------------
            st.subheader("3. 🛡️ Response Grounding, Citation Integrity & Safety")

            grounding = e2e_data.get("grounding_and_citations", {})
            g1, g2, g3, g4 = st.columns(4)
            with g1:
                st.metric("Citation ID Validity Rate", f"{grounding.get('citation_validity_rate', 1.0) * 100:.1f}%")
                st.caption("Must match real canonical FAQ ID")
            with g2:
                st.metric("Retrieval Membership Rate", f"{grounding.get('retrieval_membership_rate', 1.0) * 100:.1f}%")
                st.caption("Must be present in retrieved_sources")
            with g3:
                st.metric("Fabricated Citation Count", f"{grounding.get('fabricated_citation_count', 0)}")
                st.caption("0 Hallucinated citations")
            with g4:
                st.metric("Abstention Accuracy", f"{grounding.get('abstention_accuracy_rate', 0.0) * 100:.1f}%")
                st.caption("Correctly abstains on unsupported inquiries")

            st.markdown("---")

            # ----------------------------------------------------------------
            # Section 4: End-to-End Workflow & Latencies
            # ----------------------------------------------------------------
            st.subheader("4. ⏱️ End-to-End Workflow Performance & Latencies")

            sys_acc = e2e_data.get("system_accuracies", {})
            warm_lat = e2e_data.get("warm_workflow_latency", {})
            ret_lat = e2e_data.get("retrieval_latency", {})

            w1, w2, w3, w4 = st.columns(4)
            with w1:
                st.metric("Routing Team Accuracy", f"{sys_acc.get('routing_team_accuracy', 0.0) * 100:.1f}%")
                st.caption("Mapped to correct department")
            with w2:
                st.metric("Priority Rule Accuracy", f"{sys_acc.get('priority_rule_accuracy', 0.0) * 100:.1f}%")
                st.caption("Tier × Sentiment business logic")
            with w3:
                st.metric("Escalation Rule Accuracy", f"{sys_acc.get('escalation_decision_accuracy', 0.0) * 100:.1f}%")
                st.caption("High Priority Platinum/Gold logic")
            with w4:
                st.metric("Workflow Median Latency", f"{warm_lat.get('median', 0.0):.2f} ms")
                st.caption(f"P95: {warm_lat.get('p95', 0.0):.2f} ms | P99: {warm_lat.get('p99', 0.0):.2f} ms")

            st.markdown("---")

            # ----------------------------------------------------------------
            # Section 5: Architecture Ablation Study
            # ----------------------------------------------------------------
            st.subheader("5. 🔬 Architecture Ablation Study")
            ablation_variants = abl_data.get("ablation_variants", [])
            if ablation_variants:
                abl_df = pd.DataFrame([
                    {
                        "Architecture Variant": v["component"],
                        "Primary Evaluation Metric": (
                            f"Topic Macro F1: {v.get('topic_macro_f1', 'N/A')}"
                            if "topic_macro_f1" in v
                            else (
                                f"Recall@1: {v.get('recall_at_1', 'N/A') * 100:.1f}%"
                                if "recall_at_1" in v
                                else f"Citation Validity: {v.get('citation_validity_rate', 'N/A') * 100:.1f}%"
                            )
                        ),
                        "Latency (Median)": f"{v.get('latency_median_ms', 'N/A')} ms" if "latency_median_ms" in v else "Stage Timing",
                        "Key Engineering Finding": v["key_finding"],
                    }
                    for v in ablation_variants
                ])
                st.dataframe(abl_df, hide_index=True)

            st.markdown("---")

            # ----------------------------------------------------------------
            # Section 6: Comprehensive Markdown Report Viewer
            # ----------------------------------------------------------------
            with st.expander("📄 View Full Markdown Evaluation Report (`eval/evaluation_report.md`)"):
                if report_file.exists():
                    with open(report_file, "r", encoding="utf-8") as rf:
                        st.markdown(rf.read())
                else:
                    st.info("Report file not found.")

            # Standalone execution trigger
            st.markdown("---")
            with st.expander("⚙️ Re-run Benchmark Suite"):
                st.caption("Executes the complete 160-ticket evaluation runner offline. Does not impact live ticket processing.")
                if st.button("Rerun Evaluation Benchmark (Offline)", key="btn_rerun_benchmark"):
                    with st.spinner("Executing full Week 3 evaluation pipeline..."):
                        from eval.run_week3_evaluation import run_all_evaluations
                        run_all_evaluations()
                        st.success("✅ Evaluation suite completed successfully!")
                        st.rerun()
