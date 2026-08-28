"""Qdrant-backed hybrid vector store.

The collection carries two named vectors per point - a dense embedding and a
sparse (BM25) one - so a single query can fuse lexical and semantic matches.
With QDRANT_URL unset the client runs against a local on-disk store, which keeps
the whole pipeline runnable without Docker.
"""

from __future__ import annotations

import logging
import uuid
from collections.abc import Sequence
from typing import Any

from qdrant_client import QdrantClient, models

from advanced_rag.config import Settings, get_settings
from advanced_rag.models import Chunk, RetrievedChunk
from advanced_rag.retrieval.embeddings import Embedder, get_embedder, normalize_scores

logger = logging.getLogger(__name__)

DENSE = "dense"
SPARSE = "sparse"


class EmbeddedStoreBusyError(RuntimeError):
    """Another process holds the embedded store's exclusive lock.

    Worth its own error: the underlying message is accurate but says nothing about
    *which* processes conflict in this project, and the collision (API running
    while you re-ingest or run the eval) is the single most common local snag.
    """

    def __init__(self, path) -> None:
        super().__init__(
            f"The embedded Qdrant store at {path} is locked by another process.\n"
            "Embedded mode allows exactly one client, so `rag-api`, `rag-ingest` and\n"
            "the evaluation runner cannot overlap. Either:\n"
            "  - stop the other process (the API server is the usual culprit), or\n"
            "  - run the Qdrant container (`docker compose up -d qdrant`) and set\n"
            "    QDRANT_URL=http://localhost:6333, which supports concurrent access."
        )


class HybridStore:
    """Create, populate and query the hybrid collection."""

    def __init__(self, settings: Settings | None = None, embedder: Embedder | None = None) -> None:
        self.settings = settings or get_settings()
        self.embedder = embedder or get_embedder()
        self.collection = self.settings.qdrant_collection
        self._client: QdrantClient | None = None

    @property
    def client(self) -> QdrantClient:
        if self._client is None:
            if self.settings.use_remote_qdrant:
                logger.info("Connecting to Qdrant at %s", self.settings.qdrant_url)
                self._client = QdrantClient(
                    url=self.settings.qdrant_url,
                    api_key=self.settings.qdrant_api_key or None,
                )
            else:
                path = self.settings.absolute(self.settings.qdrant_path)
                path.mkdir(parents=True, exist_ok=True)
                logger.info("Using embedded Qdrant at %s", path)
                try:
                    self._client = QdrantClient(path=str(path))
                except RuntimeError as exc:
                    if "already accessed by another instance" not in str(exc):
                        raise
                    raise EmbeddedStoreBusyError(path) from exc
        return self._client

    # ------------------------------------------------------------- collection

    def ensure_collection(self, *, recreate: bool = False) -> None:
        exists = self.client.collection_exists(self.collection)
        if exists and recreate:
            logger.warning("Dropping existing collection %s", self.collection)
            self.client.delete_collection(self.collection)
            exists = False
        if exists:
            return

        # The keyword backend has no dense arm, so the collection is created
        # sparse-only rather than with a placeholder dense vector.
        vectors_config: dict[str, models.VectorParams] = {}
        if self.embedder.supports_dense:
            vectors_config[DENSE] = models.VectorParams(
                size=self.embedder.dim, distance=models.Distance.COSINE
            )
            logger.info("Creating collection %s (dense dim=%d + sparse)", self.collection,
                        self.embedder.dim)
        else:
            logger.info("Creating collection %s (sparse only)", self.collection)

        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=vectors_config,
            sparse_vectors_config={
                # IDF is what turns raw term frequencies into BM25 scoring.
                SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)
            },
        )
        if not self.settings.use_remote_qdrant:
            # Embedded Qdrant ignores payload indexes and warns about it. Filtering
            # still works without them, so skip the call rather than emit noise.
            return
        for field in ("doc_type", "source", "component"):
            self.client.create_payload_index(
                collection_name=self.collection,
                field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

    def count(self) -> int:
        if not self.client.collection_exists(self.collection):
            return 0
        return self.client.count(self.collection, exact=True).count

    def close(self) -> None:
        """Release the client. Matters for the embedded store's file lock."""
        if self._client is not None:
            self._client.close()
            self._client = None

    # ---------------------------------------------------------------- writing

    def upsert(self, chunks: Sequence[Chunk], batch_size: int = 64) -> int:
        self.ensure_collection()
        written = 0
        for start in range(0, len(chunks), batch_size):
            batch = list(chunks[start : start + batch_size])
            texts = [c.text for c in batch]
            sparse = self.embedder.sparse_documents(texts)
            dense = self.embedder.embed_documents(texts) if self.embedder.supports_dense else None

            points = []
            for index, (chunk, sparse_vec) in enumerate(zip(batch, sparse, strict=True)):
                vector: dict[str, Any] = {
                    SPARSE: models.SparseVector(
                        indices=sparse_vec.indices, values=sparse_vec.values
                    )
                }
                if dense is not None:
                    vector[DENSE] = dense[index]
                points.append(
                    models.PointStruct(
                        id=_point_id(chunk.id), vector=vector, payload=chunk.payload()
                    )
                )
            self.client.upsert(collection_name=self.collection, points=points)
            written += len(points)
            logger.info("Indexed %d/%d chunks", written, len(chunks))
        return written

    # ---------------------------------------------------------------- reading

    def search(
        self,
        query: str,
        *,
        top_k: int | None = None,
        mode: str = "hybrid",
        fusion: str = "weighted",
        doc_type: str | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve chunks for a query.

        mode:   dense | sparse | hybrid
        fusion: weighted (client-side, honours HYBRID_DENSE_WEIGHT) or rrf
                (server-side reciprocal rank fusion, weight-free).
        """
        top_k = top_k or self.settings.retrieve_top_k
        if not self.client.collection_exists(self.collection):
            logger.warning("Collection %s is missing - run the ingestion first", self.collection)
            return []

        query_filter = _doc_type_filter(doc_type)

        if not self.embedder.supports_dense and mode != "sparse":
            # Without a dense arm there is nothing to fuse; say so once rather
            # than failing, so callers that ask for "hybrid" still get results.
            logger.info("No dense arm available - serving %r as sparse-only", mode)
            mode = "sparse"

        if mode == "dense":
            return self._single(query, top_k, DENSE, query_filter)
        if mode == "sparse":
            return self._single(query, top_k, SPARSE, query_filter)
        if fusion == "rrf":
            return self._hybrid_rrf(query, top_k, query_filter)
        return self._hybrid_weighted(query, top_k, query_filter)

    def _single(
        self, query: str, top_k: int, using: str, query_filter: models.Filter | None
    ) -> list[RetrievedChunk]:
        vector: Any
        if using == DENSE:
            vector = self.embedder.embed_query(query)
        else:
            sparse = self.embedder.sparse_query(query)
            vector = models.SparseVector(indices=sparse.indices, values=sparse.values)

        response = self.client.query_points(
            collection_name=self.collection,
            query=vector,
            using=using,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )
        results = [_to_retrieved(p, p.score) for p in response.points]
        for rank, result in enumerate(results):
            if using == DENSE:
                result.dense_rank = rank
            else:
                result.sparse_rank = rank
        return results

    def _prefetch(self, query: str, limit: int) -> list[models.Prefetch]:
        sparse = self.embedder.sparse_query(query)
        return [
            models.Prefetch(query=self.embedder.embed_query(query), using=DENSE, limit=limit),
            models.Prefetch(
                query=models.SparseVector(indices=sparse.indices, values=sparse.values),
                using=SPARSE,
                limit=limit,
            ),
        ]

    def _hybrid_rrf(
        self, query: str, top_k: int, query_filter: models.Filter | None
    ) -> list[RetrievedChunk]:
        """Server-side reciprocal rank fusion - one round trip, no tunable weight."""
        response = self.client.query_points(
            collection_name=self.collection,
            prefetch=self._prefetch(query, top_k),
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )
        return [_to_retrieved(p, p.score) for p in response.points]

    def _hybrid_weighted(
        self, query: str, top_k: int, query_filter: models.Filter | None
    ) -> list[RetrievedChunk]:
        """Client-side fusion of min-max normalised dense and sparse scores.

        Slightly more work than RRF, but HYBRID_DENSE_WEIGHT becomes a real dial:
        push it up for paraphrased questions, down for exact error strings and
        resource names - which is most of Kubernetes troubleshooting.
        """
        weight = self.settings.hybrid_dense_weight
        # Over-fetch each arm so the fused top_k is drawn from a wider pool.
        pool = max(top_k * 2, top_k + 10)
        dense_hits = self._single(query, pool, DENSE, query_filter)
        sparse_hits = self._single(query, pool, SPARSE, query_filter)

        merged: dict[str, RetrievedChunk] = {}
        for hits, arm_weight, is_dense in (
            (dense_hits, weight, True),
            (sparse_hits, 1.0 - weight, False),
        ):
            normalized = normalize_scores(h.retrieval_score for h in hits)
            for score, hit in zip(normalized, hits, strict=True):
                existing = merged.get(hit.chunk.id)
                if existing is None:
                    hit.retrieval_score = score * arm_weight
                    merged[hit.chunk.id] = hit
                    continue
                existing.retrieval_score += score * arm_weight
                if is_dense:
                    existing.dense_rank = hit.dense_rank
                else:
                    existing.sparse_rank = hit.sparse_rank

        ranked = sorted(merged.values(), key=lambda r: r.retrieval_score, reverse=True)
        return ranked[:top_k]


def _doc_type_filter(doc_type: str | None) -> models.Filter | None:
    if not doc_type:
        return None
    return models.Filter(
        must=[models.FieldCondition(key="doc_type", match=models.MatchValue(value=doc_type))]
    )


def _point_id(chunk_id: str) -> str:
    """Qdrant point IDs must be UUIDs or unsigned ints; derive one deterministically."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def _to_retrieved(point: Any, score: float) -> RetrievedChunk:
    payload = dict(point.payload or {})
    known = {"chunk_id", "text", "source", "title", "section", "doc_type"}
    chunk = Chunk(
        id=payload.get("chunk_id") or str(point.id),
        text=payload.get("text", ""),
        source=payload.get("source", ""),
        title=payload.get("title", ""),
        section=payload.get("section", ""),
        doc_type=payload.get("doc_type", "runbook"),
        metadata={k: v for k, v in payload.items() if k not in known},
    )
    return RetrievedChunk(chunk=chunk, retrieval_score=float(score))


_store: HybridStore | None = None


def get_store() -> HybridStore:
    global _store
    if _store is None:
        _store = HybridStore()
    return _store
