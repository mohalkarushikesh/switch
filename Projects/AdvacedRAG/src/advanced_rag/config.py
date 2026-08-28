"""Central configuration.

Every external service is optional: leaving its URL/DSN blank selects a local
fallback (embedded Qdrant, SQLite, in-process cache) so the pipeline runs on a
laptop with no Docker.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---------- LLM ----------
    anthropic_api_key: str | None = None
    llm_model: str = "claude-opus-5"
    #: Cheaper model for the many small classification/grading calls in the graph.
    llm_fast_model: str = "claude-haiku-4-5"
    llm_effort: str = "high"
    llm_max_tokens: int = 16_000
    llm_refusal_fallbacks: bool = True

    # ---------- Vector store ----------
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_path: Path = Path("data/qdrant")
    qdrant_collection: str = "k8s_ops"

    # ---------- Embeddings / reranking ----------
    #: "fastembed" = dense + sparse + cross-encoder (downloads ONNX models).
    #: "keyword"   = pure-Python BM25 only; no download, no dense arm, no reranker.
    #: "auto"      = try fastembed, fall back to keyword if the models cannot be got.
    retrieval_backend: Literal["auto", "fastembed", "keyword"] = "auto"
    dense_model: str = "BAAI/bge-small-en-v1.5"
    sparse_model: str = "Qdrant/bm25"
    rerank_model: str = "Xenova/ms-marco-MiniLM-L-6-v2"
    #: Where fastembed keeps downloaded ONNX models. Point this at a pre-populated
    #: directory on a network that blocks huggingface.co.
    model_cache_dir: Path | None = None
    #: Hugging Face token, used only to authenticate model downloads. Read from
    #: .env (gitignored) and exported to HF_TOKEN for huggingface_hub.
    hf_token: str | None = None

    # ---------- Text2SQL store ----------
    postgres_dsn: str | None = None
    sqlite_path: Path = Path("data/ops.db")
    sql_row_limit: int = 200
    sql_timeout_seconds: int = 15

    # ---------- Cache ----------
    redis_url: str | None = None
    cache_ttl_seconds: int = 3600
    semantic_cache_threshold: float = 0.95

    # ---------- Retrieval tuning ----------
    chunk_size: int = 900
    chunk_overlap: int = 150
    retrieve_top_k: int = 20
    rerank_top_n: int = 5
    hybrid_dense_weight: float = Field(0.7, ge=0.0, le=1.0)
    #: CRAG: below this reranker score the context is considered insufficient.
    crag_relevance_floor: float = 0.25
    #: Self-RAG: max answer regeneration attempts.
    self_rag_max_retries: int = 1

    # ---------- Feature flags ----------
    enable_hyde: bool = True
    enable_crag: bool = True
    enable_self_rag: bool = True
    enable_text2sql: bool = True
    enable_guardrails: bool = True
    enable_cache: bool = True

    # ---------- API ----------
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    log_level: str = "INFO"

    @property
    def use_remote_qdrant(self) -> bool:
        return bool(self.qdrant_url)

    @property
    def sql_url(self) -> str:
        """SQLAlchemy URL for the Text2SQL store, with a SQLite fallback."""
        if self.postgres_dsn:
            return self.postgres_dsn
        path = self.absolute(self.sqlite_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+pysqlite:///{path.as_posix()}"

    @property
    def sql_dialect(self) -> str:
        return "PostgreSQL" if self.postgres_dsn else "SQLite"

    def absolute(self, path: Path) -> Path:
        """Resolve a configured path relative to the project root."""
        return path if path.is_absolute() else PROJECT_ROOT / path


@lru_cache
def get_settings() -> Settings:
    return Settings()
