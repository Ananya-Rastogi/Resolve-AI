"""
Comprehensive unit and integration test suite for Week 2 RAG pipeline.
Tests adhere to Phase 15 requirements:
1. CSV deduplication
2. Canonical FAQ count
3. Document creation
4. Metadata preservation
5. Embedding generation
6. Chroma indexing
7. Retrieval
8. top_k
9. metadata filtering
10. RAG node
11. TicketState updates
12. citation generation
13. empty retrieval
14. vector DB failure handling
15. existing LangGraph flow
16. offline / mock components
"""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock

from app.models.schemas import CustomerTier, TicketState
from app.rag.chunker import chunk_documents, inspect_document_lengths
from app.rag.embeddings import MockEmbeddings, SentenceTransformerEmbeddings, get_embedding_model
from app.rag.loader import Document, format_faq_document_text, load_canonical_faqs
from app.rag.pipeline import RAGPipeline
from app.rag.prompts import TOPIC_TO_CATEGORIES_MAP
from app.rag.retriever import FAQRetriever, RetrievedDocument
from app.rag.vector_store import ChromaVectorStore
from app.graph.workflow import rag_retrieval_node, run_ticket_workflow


class TestRAGPipeline(unittest.TestCase):
    """Test suite covering Week 2 RAG requirements."""

    @classmethod
    def setUpClass(cls):
        cls.base_dir = Path(__file__).resolve().parent.parent
        cls.faq_csv_path = cls.base_dir / "data" / "rag_faqs.csv"
        cls.chroma_dir = cls.base_dir / "data" / "chroma"
        # Pre-warmup the retriever to avoid cold-start timing variations
        retriever = FAQRetriever(vector_store=ChromaVectorStore())
        retriever.retrieve("warmup inquiry", top_k=1)

    def test_1_csv_deduplication(self):
        """1. Verify CSV deduplication produced canonical dataset."""
        self.assertTrue(self.faq_csv_path.exists(), "data/rag_faqs.csv must exist.")
        docs = load_canonical_faqs(self.faq_csv_path)
        self.assertEqual(len(docs), 30)

        answers = [doc.metadata.get("answer", "") for doc in docs]
        self.assertEqual(len(set(answers)), 30, "Each of the 30 canonical records must have a unique answer.")

    def test_2_canonical_faq_count(self):
        """2. Verify canonical FAQ count is exactly 30."""
        import pandas as pd
        df = pd.read_csv(self.faq_csv_path)
        self.assertEqual(len(df), 30, "Canonical FAQ dataset should contain exactly 30 records.")

    def test_3_document_creation(self):
        """3. Verify structured Document objects are properly created."""
        sample_row = {
            "question": "How do I return an item?",
            "alternative_question": "How do I return an item? Please help.",
            "answer": "Start a return request from order history.",
            "keywords": "return, item",
        }
        text = format_faq_document_text(sample_row)
        self.assertIn("Question: How do I return an item?", text)
        self.assertIn("Alternative Query: How do I return an item? Please help.", text)
        self.assertIn("Answer: Start a return request from order history.", text)
        self.assertIn("Keywords: return, item", text)

    def test_4_metadata_preservation(self):
        """4. Verify essential metadata fields are preserved."""
        docs = load_canonical_faqs(self.faq_csv_path)
        first_meta = docs[0].metadata
        expected_fields = [
            "faq_id", "category", "subcategory", "intent",
            "response_type", "difficulty_level", "language", "canonical_answer_id"
        ]
        for field in expected_fields:
            self.assertIn(field, first_meta, f"Metadata must preserve '{field}'")
            self.assertIsNotNone(first_meta[field])

    def test_5_embedding_generation(self):
        """5. Verify embedding generation outputs correct dimensionality."""
        mock_emb = MockEmbeddings(dim=384)
        texts = ["How do I track my order?", "Where is my refund?"]
        doc_vectors = mock_emb.embed_documents(texts)
        self.assertEqual(len(doc_vectors), 2)
        self.assertEqual(len(doc_vectors[0]), 384)

        query_vec = mock_emb.embed_query("order tracking")
        self.assertEqual(len(query_vec), 384)

    def test_6_chroma_indexing(self):
        """6. Verify Chroma vector store indexing."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            store = ChromaVectorStore(
                persist_directory=tmpdir,
                collection_name="test_indexing_collection",
                embedding_model=MockEmbeddings(dim=384),
            )
            sample_docs = [
                Document(text="Question: How do I reset password?\nAnswer: Click forgot password.", doc_id="FAQ_T1", metadata={"category": "Account_Access"}),
                Document(text="Question: Where is my invoice?\nAnswer: Download from account.", doc_id="FAQ_T2", metadata={"category": "Billing"}),
            ]
            indexed_count = store.add_documents(sample_docs)
            self.assertEqual(indexed_count, 2)
            self.assertEqual(store.count(), 2)

    def test_7_retrieval(self):
        """7. Verify semantic retrieval returns valid relevance scores and texts."""
        store = ChromaVectorStore()
        retriever = FAQRetriever(vector_store=store, default_top_k=3)
        docs, latency_ms = retriever.retrieve("I was charged twice for my subscription")

        self.assertGreater(len(docs), 0)
        self.assertLess(latency_ms, 500.0)
        first_doc = docs[0]
        self.assertIsInstance(first_doc, RetrievedDocument)
        self.assertTrue(first_doc.faq_id.startswith("FAQ_"))
        self.assertGreaterEqual(first_doc.score, 0.0)
        self.assertLessEqual(first_doc.score, 1.0)

    def test_8_top_k(self):
        """8. Verify top_k parameter restricts results appropriately."""
        store = ChromaVectorStore()
        retriever = FAQRetriever(vector_store=store)

        docs_top2, _ = retriever.retrieve("shipping cost", top_k=2)
        self.assertEqual(len(docs_top2), 2)

        docs_top5, _ = retriever.retrieve("shipping cost", top_k=5)
        self.assertEqual(len(docs_top5), 5)

    def test_9_metadata_filtering(self):
        """9. Verify topic-based category filtering."""
        store = ChromaVectorStore()
        retriever = FAQRetriever(vector_store=store, default_top_k=3)

        # Query with topic 'billing'
        docs, _ = retriever.retrieve(
            query="When will I receive my money back?",
            filter_topic="billing",
            strict_category_filter=True,
        )
        self.assertGreater(len(docs), 0)
        allowed_billing_cats = set(TOPIC_TO_CATEGORIES_MAP["billing"])
        for doc in docs:
            self.assertIn(doc.category, allowed_billing_cats)

    def test_10_rag_node(self):
        """10. Verify rag_retrieval_node updates state in LangGraph workflow."""
        state = TicketState(
            subject="I can't log into my account, password reset link not working",
            ticket_id="TKT-TEST-RAG-NODE",
            topic="technical",
            priority="High",
            routed_to="Technical Support",
            escalation="No Escalation Required",
        )
        updated_dict = rag_retrieval_node(state)
        updated_state = TicketState(**updated_dict)

        self.assertTrue(updated_state.rag_used)
        self.assertGreater(updated_state.retrieval_count, 0)
        self.assertIsNotNone(updated_state.retrieved_context)
        self.assertIn("FAQ_", updated_state.retrieved_context)
        self.assertIsNotNone(updated_state.retrieval_latency_ms)

    def test_11_ticket_state_updates(self):
        """11. Verify all Week 2 RAG fields in TicketState."""
        pipeline = RAGPipeline()
        state = TicketState(
            subject="How do I return something I bought?",
            topic="shipping",
        )
        processed = pipeline.process_ticket(state, top_k=2)

        self.assertEqual(processed.rag_query, "How do I return something I bought?")
        self.assertTrue(processed.rag_used)
        self.assertEqual(processed.retrieval_count, 2)
        self.assertEqual(len(processed.retrieved_sources), 2)
        self.assertEqual(len(processed.retrieval_scores), 2)
        self.assertEqual(len(processed.retrieval_metadata), 2)
        self.assertIsNone(processed.rag_error)

    def test_12_citation_generation(self):
        """12. Verify citation metadata and traceability."""
        doc = RetrievedDocument(
            faq_id="FAQ_001",
            category="Payment_Issue",
            score=0.8876,
            text="Question: Payment methods\nAnswer: Cards accepted.",
            metadata={"category": "Payment_Issue"},
        )
        citation = doc.to_citation()
        self.assertEqual(citation["faq_id"], "FAQ_001")
        self.assertEqual(citation["category"], "Payment_Issue")
        self.assertEqual(citation["score"], 0.8876)

    def test_13_empty_retrieval(self):
        """13. Verify empty retrieval handling without errors."""
        retriever = FAQRetriever(vector_store=ChromaVectorStore())
        docs, latency_ms = retriever.retrieve("")
        self.assertEqual(docs, [])
        self.assertGreaterEqual(latency_ms, 0.0)

    def test_14_vector_db_failure_handling(self):
        """14. Verify graceful degradation when vector database fails."""
        mock_store = MagicMock()
        mock_store.query.side_effect = RuntimeError("Simulated ChromaDB connection timeout")
        failing_retriever = FAQRetriever(vector_store=mock_store)
        pipeline = RAGPipeline(retriever=failing_retriever)

        state = TicketState(
            subject="Why was I charged twice?",
            topic="billing",
        )
        processed = pipeline.process_ticket(state)

        # Workflow must not crash; error recorded
        self.assertFalse(processed.rag_used)
        self.assertIsNotNone(processed.rag_error)
        self.assertIn("Simulated ChromaDB connection timeout", processed.rag_error)

    def test_15_langgraph_flow_with_rag(self):
        """15. Verify complete LangGraph flow with classification -> ... -> rag_retrieval -> response."""
        state = TicketState(
            subject="I was charged twice for my subscription renewal",
            tier=CustomerTier.GOLD,
        )
        result = run_ticket_workflow(state)

        self.assertIsNotNone(result.ticket_id)
        self.assertEqual(result.topic, "billing")
        self.assertTrue(result.rag_used)
        self.assertGreater(result.retrieval_count, 0)
        self.assertIn("Sources:", result.final_response)
        self.assertIn("FAQ_", result.final_response)

    def test_16_offline_mock_components(self):
        """16. Verify offline mock embeddings execute without network access."""
        mock_emb = get_embedding_model(use_mock=True)
        self.assertIsInstance(mock_emb, MockEmbeddings)
        vec = mock_emb.embed_query("test query without network")
        self.assertEqual(len(vec), 384)

    def test_17_embedding_model_reuse(self):
        """17. Verify embedding model instances and underlying weights are reused across calls."""
        model_1 = get_embedding_model()
        model_2 = get_embedding_model()
        self.assertIs(model_1, model_2, "get_embedding_model must return cached singleton instance.")

        # Verify underlying SentenceTransformer object is identical
        underlying_1 = model_1._get_model()
        underlying_2 = model_2._get_model()
        self.assertIs(underlying_1, underlying_2, "SentenceTransformer weights must not be reloaded.")

    def test_18_chroma_client_reuse(self):
        """18. Verify ChromaDB PersistentClient and collection are reused across instances."""
        store_1 = ChromaVectorStore()
        store_2 = ChromaVectorStore()

        client_1 = store_1._get_client()
        client_2 = store_2._get_client()
        self.assertIs(client_1, client_2, "Chroma PersistentClient must be reused across store instances.")

        col_1 = store_1.get_collection()
        col_2 = store_2.get_collection()
        self.assertIs(col_1, col_2, "Chroma collection must be reused across store instances.")

    def test_19_warm_retrieval_latency_instrumentation(self):
        """19. Verify detailed timing instrumentation (embedding_query_ms, vector_search_ms, total_retrieval_ms)."""
        retriever = FAQRetriever(vector_store=ChromaVectorStore())
        docs, latency_ms = retriever.retrieve("How do I return an item?")

        self.assertIn("embedding_query_ms", retriever.last_timings)
        self.assertIn("vector_search_ms", retriever.last_timings)
        self.assertIn("total_retrieval_ms", retriever.last_timings)
        self.assertIn("is_cold", retriever.last_timings)

        self.assertGreaterEqual(retriever.last_timings["embedding_query_ms"], 0.0)
        self.assertGreaterEqual(retriever.last_timings["vector_search_ms"], 0.0)
        self.assertGreater(retriever.last_timings["total_retrieval_ms"], 0.0)
        # Warm inference should be well below 500ms
        self.assertLess(retriever.last_timings["total_retrieval_ms"], 500.0)

        # Test TicketState integration in RAGPipeline
        pipeline = RAGPipeline(retriever=retriever)
        state = TicketState(subject="How do I return an item?", topic="shipping")
        processed = pipeline.process_ticket(state)
        self.assertIsNotNone(processed.embedding_query_ms)
        self.assertIsNotNone(processed.vector_search_ms)
        self.assertIsNotNone(processed.total_retrieval_ms)
        self.assertFalse(processed.is_cold_retrieval)

    def test_20_retrieved_sources_preserved_and_used_sources_tracked(self):
        """20. Verify retrieved sources are preserved while used sources are separately tracked."""
        state = TicketState(
            subject="I was charged twice for my subscription renewal",
            tier=CustomerTier.GOLD,
        )
        result = run_ticket_workflow(state)

        # Preserved retrieved sources (all 3 documents)
        self.assertEqual(len(result.retrieved_sources), 3, "All retrieved sources must be preserved for transparency.")
        for src in result.retrieved_sources:
            self.assertIn("faq_id", src)
            self.assertIn("category", src)
            self.assertIn("score", src)

        # Separately tracked used sources / citations
        self.assertIsInstance(result.used_sources, list)
        self.assertGreater(len(result.used_sources), 0)
        # Only the primary supporting FAQ should be cited in Mock LLM output
        self.assertLess(len(result.used_sources), len(result.retrieved_sources))
        self.assertIn(result.used_sources[0]["faq_id"], result.final_response)

    def test_21_citation_ids_must_correspond_to_retrieved_documents(self):
        """21. Verify citation IDs strictly correspond to retrieved documents and cannot be fabricated."""
        from app.agents.response import extract_used_sources

        retrieved = [
            {"faq_id": "FAQ_010", "category": "Payment_Issue", "score": 0.70},
            {"faq_id": "FAQ_003", "category": "Shipping_Info", "score": 0.49},
            {"faq_id": "FAQ_025", "category": "Complaint", "score": 0.25},
        ]

        # Case: Response references FAQ_010 and fabricated FAQ_999
        response_with_hallucination = (
            "Based on our policy in FAQ_010 and also external FAQ_999, your refund is processed."
        )
        used = extract_used_sources(response_with_hallucination, retrieved)

        used_ids = [s["faq_id"] for s in used]
        self.assertIn("FAQ_010", used_ids)
        self.assertNotIn("FAQ_999", used_ids, "Fabricated FAQ_999 must not be included in used citations.")
        self.assertEqual(len(used), 1)

    def test_22_multiple_citations_allowed_when_genuinely_used(self):
        """22. Verify multiple citations are tracked when the response genuinely uses multiple retrieved docs."""
        from app.agents.response import extract_used_sources

        retrieved = [
            {"faq_id": "FAQ_010", "category": "Payment_Issue", "score": 0.70},
            {"faq_id": "FAQ_003", "category": "Shipping_Info", "score": 0.49},
            {"faq_id": "FAQ_025", "category": "Complaint", "score": 0.25},
        ]

        response_with_multi = (
            "We have reviewed your inquiry.\n\n"
            "Sources:\n"
            "- FAQ_010 (Category: Payment_Issue)\n"
            "- FAQ_003 (Category: Shipping_Info)"
        )
        used = extract_used_sources(response_with_multi, retrieved)

        used_ids = [s["faq_id"] for s in used]
        self.assertEqual(used_ids, ["FAQ_010", "FAQ_003"])
        self.assertNotIn("FAQ_025", used_ids)

    def test_23_no_citations_when_none_used(self):
        """23. Verify citation list is empty when no retrieved documents supported the response."""
        from app.agents.response import extract_used_sources

        retrieved = [
            {"faq_id": "FAQ_010", "category": "Payment_Issue", "score": 0.70},
        ]
        response_without_sources = "Our team will manually review your inquiry shortly."
        used = extract_used_sources(response_without_sources, retrieved)
        self.assertEqual(used, [])


if __name__ == "__main__":
    unittest.main()
