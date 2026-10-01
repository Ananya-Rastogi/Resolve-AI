"""
Chroma vector database integration and index building for FAQ knowledge.

Persists embeddings and metadata locally in data/chroma/.
Provides CLI entrypoint:
    python -m app.rag.vector_store --build [--force]
"""
import argparse
import logging
from pathlib import Path
from typing import Any, Optional
from app.rag.chunker import chunk_documents
from app.rag.embeddings import BaseEmbeddingModel, get_embedding_model
from app.rag.loader import Document, load_canonical_faqs

logger = logging.getLogger(__name__)

DEFAULT_CHROMA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "chroma"
DEFAULT_COLLECTION_NAME = "faq_knowledge_base"


_GLOBAL_CHROMA_CLIENTS: dict[str, Any] = {}
_GLOBAL_CHROMA_COLLECTIONS: dict[tuple[str, str], Any] = {}
_GLOBAL_VECTOR_STORES: dict[tuple[str, str], "ChromaVectorStore"] = {}


def reset_vector_store_cache():
    """Reset cached ChromaDB clients, collections, and store instances (used for testing)."""
    global _GLOBAL_CHROMA_CLIENTS, _GLOBAL_CHROMA_COLLECTIONS, _GLOBAL_VECTOR_STORES
    _GLOBAL_CHROMA_CLIENTS.clear()
    _GLOBAL_CHROMA_COLLECTIONS.clear()
    _GLOBAL_VECTOR_STORES.clear()


class ChromaVectorStore:
    """
    Manages local persistent vector storage using ChromaDB.
    Stores document text, computed embeddings, metadata, and unique document IDs.
    Reuses persistent client and collection instances across tickets.
    """

    def __init__(
        self,
        persist_directory: Optional[Path | str] = None,
        collection_name: str = DEFAULT_COLLECTION_NAME,
        embedding_model: Optional[BaseEmbeddingModel] = None,
    ):
        self.persist_directory = Path(persist_directory) if persist_directory else DEFAULT_CHROMA_DIR
        self.collection_name = collection_name
        self.embedding_model = embedding_model or get_embedding_model()
        self._client = None
        self._collection = None
        self.last_query_timings: dict[str, float] = {
            "embedding_query_ms": 0.0,
            "vector_search_ms": 0.0,
            "total_ms": 0.0,
        }

    def _get_client(self):
        """Lazy initialization with process-wide caching of ChromaDB PersistentClient."""
        cache_key = str(self.persist_directory.resolve())
        if cache_key not in _GLOBAL_CHROMA_CLIENTS:
            import chromadb
            from chromadb.config import Settings
            self.persist_directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Initializing persistent ChromaDB client at '{cache_key}' (cached globally)...")
            _GLOBAL_CHROMA_CLIENTS[cache_key] = chromadb.PersistentClient(
                path=str(self.persist_directory),
                settings=Settings(anonymized_telemetry=False),
            )
        self._client = _GLOBAL_CHROMA_CLIENTS[cache_key]
        return self._client

    def get_collection(self):
        """Retrieve or create the FAQ collection with global caching."""
        cache_key = (str(self.persist_directory.resolve()), self.collection_name)
        if cache_key not in _GLOBAL_CHROMA_COLLECTIONS:
            client = self._get_client()
            logger.info(f"Retrieving or creating Chroma collection '{self.collection_name}' (cached globally)...")
            _GLOBAL_CHROMA_COLLECTIONS[cache_key] = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Customer Support Canonical FAQ Knowledge Base"},
            )
        self._collection = _GLOBAL_CHROMA_COLLECTIONS[cache_key]
        return self._collection

    def count(self) -> int:
        """Return the number of indexed documents in the collection."""
        try:
            return self.get_collection().count()
        except Exception as e:
            logger.warning(f"Could not count collection items: {e}")
            return 0

    def add_documents(
        self,
        documents: list[Document],
        batch_size: int = 100,
    ) -> int:
        """
        Embed and persist documents into ChromaDB.
        """
        if not documents:
            return 0

        collection = self.get_collection()

        ids = [doc.doc_id or f"doc_{i}" for i, doc in enumerate(documents)]
        texts = [doc.text for doc in documents]
        metadatas = [doc.metadata for doc in documents]

        # Compute embeddings via configured embedding model
        logger.info(f"Computing embeddings for {len(documents)} documents...")
        embeddings = self.embedding_model.embed_documents(texts)

        # Upsert into collection in batches
        for i in range(0, len(documents), batch_size):
            end_idx = min(i + batch_size, len(documents))
            collection.upsert(
                ids=ids[i:end_idx],
                embeddings=embeddings[i:end_idx],
                documents=texts[i:end_idx],
                metadatas=metadatas[i:end_idx],
            )

        logger.info(f"Successfully indexed {len(documents)} documents into '{self.collection_name}'.")
        return len(documents)

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        where: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Execute vector similarity search for a query string with granular timing instrumentation.
        
        Returns:
            list of dicts containing:
            - text: document string
            - faq_id: identifier
            - score: cosine similarity / relevance score [0.0 - 1.0]
            - metadata: document metadata dict
        """
        import time
        t_start = time.perf_counter()
        collection = self.get_collection()
        total_docs = collection.count()
        if total_docs == 0:
            logger.warning("Query attempted against empty Chroma vector store.")
            self.last_query_timings = {
                "embedding_query_ms": 0.0,
                "vector_search_ms": 0.0,
                "total_ms": round((time.perf_counter() - t_start) * 1000, 2),
            }
            return []

        actual_k = min(top_k, total_docs)

        t_embed_start = time.perf_counter()
        query_embedding = self.embedding_model.embed_query(query_text)
        embedding_query_ms = round((time.perf_counter() - t_embed_start) * 1000, 2)

        query_kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": actual_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_kwargs["where"] = where

        t_search_start = time.perf_counter()
        try:
            results = collection.query(**query_kwargs)
        except Exception as e:
            logger.error(f"Chroma query failed: {e}. Retrying without metadata filter if filter was active...")
            if where:
                query_kwargs.pop("where", None)
                results = collection.query(**query_kwargs)
            else:
                raise
        vector_search_ms = round((time.perf_counter() - t_search_start) * 1000, 2)
        total_query_ms = round((time.perf_counter() - t_start) * 1000, 2)

        self.last_query_timings = {
            "embedding_query_ms": embedding_query_ms,
            "vector_search_ms": vector_search_ms,
            "total_ms": total_query_ms,
        }

        retrieved: list[dict[str, Any]] = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return retrieved

        ids = results["ids"][0]
        docs = results["documents"][0] if results.get("documents") else [""] * len(ids)
        metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids)
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)

        for doc_id, text, meta, dist in zip(ids, docs, metas, distances):
            score = max(0.0, min(1.0, 1.0 - (float(dist) / 2.0)))
            faq_id = meta.get("faq_id", doc_id) if meta else doc_id

            retrieved.append({
                "faq_id": str(faq_id),
                "text": text,
                "score": round(score, 4),
                "distance": round(float(dist), 4),
                "metadata": meta or {},
            })

        return retrieved

    def build_index(
        self,
        csv_path: Optional[Path | str] = None,
        force_rebuild: bool = False,
    ) -> int:
        """
        Build or update the Chroma vector index from canonical FAQ CSV.
        If index already exists and force_rebuild is False, reuses existing index.
        """
        existing_count = self.count()
        if existing_count > 0 and not force_rebuild:
            logger.info(
                f"Vector database already contains {existing_count} documents. "
                "Reusing existing index (use force_rebuild=True to overwrite)."
            )
            return existing_count

        cache_key = (str(self.persist_directory.resolve()), self.collection_name)
        if force_rebuild and self._client is not None:
            try:
                self._client.delete_collection(self.collection_name)
                self._collection = None
                _GLOBAL_CHROMA_COLLECTIONS.pop(cache_key, None)
                logger.info(f"Cleared existing collection '{self.collection_name}'.")
            except Exception as e:
                logger.warning(f"Could not delete collection during force rebuild: {e}")

        docs = load_canonical_faqs(csv_path)
        chunks = chunk_documents(docs)
        count = self.add_documents(chunks)
        return count


def get_vector_store(
    persist_directory: Optional[Path | str] = None,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    embedding_model: Optional[BaseEmbeddingModel] = None,
) -> ChromaVectorStore:
    """
    Factory function retrieving or creating a process-wide singleton ChromaVectorStore.
    """
    target_dir = Path(persist_directory) if persist_directory else DEFAULT_CHROMA_DIR
    key = (str(target_dir.resolve()), collection_name)
    if key not in _GLOBAL_VECTOR_STORES:
        _GLOBAL_VECTOR_STORES[key] = ChromaVectorStore(
            persist_directory=target_dir,
            collection_name=collection_name,
            embedding_model=embedding_model,
        )
    return _GLOBAL_VECTOR_STORES[key]


def main():
    """CLI entrypoint to build the vector store."""
    parser = argparse.ArgumentParser(description="Build customer support RAG vector index in ChromaDB.")
    parser.add_argument("--build", action="store_true", help="Build or update the vector store")
    parser.add_argument("--force", action="store_true", help="Force rebuild, clearing existing index")
    parser.add_argument("--csv", type=str, default=None, help="Path to canonical FAQ CSV file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    store = ChromaVectorStore()
    if args.build or args.force:
        logger.info("Starting FAQ vector index build...")
        count = store.build_index(csv_path=args.csv, force_rebuild=args.force)
        logger.info(f"RAG vector index ready with {count} documents.")
    else:
        count = store.count()
        logger.info(f"Chroma vector store currently has {count} documents. Run with --build to index.")


if __name__ == "__main__":
    main()
