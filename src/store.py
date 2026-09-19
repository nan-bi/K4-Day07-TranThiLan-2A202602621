from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Uses an in-memory store. ChromaDB is intentionally disabled to avoid
    the trap where self._use_chroma = True is set before the client is created,
    causing all methods to fail if chromadb happens to be installed.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        # ChromaDB branch intentionally disabled — no test requires it,
        # requirements.txt doesn't install it, and the initialization has a trap.

    def _make_record(self, doc: Document) -> dict[str, Any]:
        """Build a normalized stored record for one document.

        Copies metadata to avoid mutating the caller's object.
        Always injects 'doc_id' into metadata so delete_document can find it.
        """
        embedding = self._embedding_fn(doc.content)
        # Copy metadata instead of mutating caller's dict
        meta = dict(doc.metadata)
        meta["doc_id"] = doc.id
        record = {
            "id": f"{doc.id}_{self._next_index}",
            "content": doc.content,
            "metadata": meta,
            "embedding": embedding,
        }
        self._next_index += 1
        return record

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        """Run in-memory similarity search over provided records.

        Returns results without the embedding vector (keeps output clean).
        """
        if not records:
            return []

        query_embedding = self._embedding_fn(query)

        scored: list[dict[str, Any]] = []
        for record in records:
            # MockEmbedder produces normalized vectors (||v||=1),
            # so dot product equals cosine similarity.
            score = _dot(query_embedding, record["embedding"])
            scored.append({
                "content": record["content"],
                "metadata": record["metadata"],
                "score": score,
            })

        # Sort by score descending
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        Each Document becomes exactly one record (1 Document = 1 record).
        Chunking happens at a layer above — the caller is responsible for
        splitting text into chunks and creating separate Documents.
        """
        for doc in docs:
            record = self._make_record(doc)
            self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        Embeds query, computes dot product vs all stored embeddings,
        returns top_k sorted by score descending.
        """
        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        IMPORTANT: Filters BEFORE search (not after). If you search first
        then filter, top-k slots may be filled by irrelevant docs and you
        get 0 results even though matching docs exist in the store.
        """
        if metadata_filter is None:
            return self.search(query, top_k)

        # Pre-filter records by metadata
        filtered_records = []
        for record in self._store:
            match = True
            for key, value in metadata_filter.items():
                if record["metadata"].get(key) != value:
                    match = False
                    break
            if match:
                filtered_records.append(record)

        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Matches on metadata['doc_id'] — this is why _make_record always
        injects doc_id into the metadata dict.

        Returns True if any chunks were removed, False otherwise.
        """
        original_size = len(self._store)
        self._store = [
            record for record in self._store
            if record["metadata"].get("doc_id") != doc_id
        ]
        return len(self._store) < original_size
