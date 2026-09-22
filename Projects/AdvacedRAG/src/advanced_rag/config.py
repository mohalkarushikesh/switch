"""Central configuration.

Every external service is optional: leaving its URL/DSN blank selects a local
fallback (embedded Qdrant, SQLite, in-process cache) so the pipeline runs on a
laptop with no Docker.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---------- LLM ----------
    #: Which LLM backend the graph/guardrails call through. "anthropic" = Claude
    #: via the Anthropic SDK; "gemini" = Google Gemini via the google-genai SDK;
    #: "offline" = no model at all, which makes generation extractive (the
    #: retrieved passages are quoted instead of synthesised). Offline mode is
    #: also selected automatically when the chosen provider has no credentials.
    llm_provider: Literal["anthropic", "gemini", "offline"] = "anthropic"
    anthropic_api_key: str | None = None
    #: Gemini API key (Google AI Studio). Only used when llm_provider == "gemini".
    #: Accepts either GEMINI_API_KEY (the name Google AI Studio hands out) or
    #: GOOGLE_API_KEY; the google-genai SDK itself only reads them from the OS
    #: environment, so loading it here from .env is what actually wires it up.
    google_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY", "google_api_key"),
    )
    llm_model: str = "claude-opus-5"
    #: Cheaper model for the many small classification/grading calls in the graph.
    llm_fast_model: str = "claude-haiku-4-5"
    llm_effort: str = "high"
    llm_max_tokens: int = 16_000
    llm_refusal_fallbacks: bool = True
    #: Bounded retry for transient Gemini 429/5xx (flash "high demand" 503s).
    #: 1 disables retrying. Applies to the gemini backend's chat path.
    llm_max_retries: int = 4
    #: If the primary model still fails with a transient error after retries, try
    #: once on this model. Empty disables it. Point it at the fast model to keep
    #: interactive latency bounded when the main model is being load-shed.
    llm_retry_fallback_model: str | None = None

    # ---------- Vector store ----------
    qdrant_url: str | None = None
    qdrant_api_key: str | None = None
    qdrant_path: Path = Path("data/qdrant")
    qdrant_collection: str = "k8s_ops"

    # ---------- Embeddings / reranking ----------
    #: "fastembed" = dense + sparse + cross-encoder (downloads ONNX models).
    #: "keyword"   = pure-Python BM25 only; no download, no dense arm, no reranker.
    #: "gemini"    = dense via the Gemini embeddings API + sparse via local BM25.
    #:              The on-network path to a real dense arm where huggingface.co
    #:              is blocked but the Gemini API is reachable. No cross-encoder
    #:              (that stays the lexical stand-in), no ONNX download.
    #: "auto"      = try fastembed, fall back to keyword if the models cannot be got.
    retrieval_backend: Literal["auto", "fastembed", "keyword", "gemini"] = "auto"
    dense_model: str = "BAAI/bge-small-en-v1.5"
    sparse_model: str = "Qdrant/bm25"
    rerank_model: str = "Xenova/ms-marco-MiniLM-L-6-v2"
    #: Gemini embedding model + output width, used only when retrieval_backend ==
    #: "gemini". gemini-embedding-001 emits 3072 dims by default but supports
    #: Matryoshka truncation; 768 keeps the Qdrant collection lean at negligible
    #: quality cost. Reuses google_api_key (GEMINI_API_KEY).
    embed_model: str = "gemini-embedding-001"
    embed_dim: int = 768
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

    # ---------- Graph state ----------
    #: "memory" keeps SQL-approval run state in-process (single replica / sticky).
    #: "postgres" persists it via langgraph-checkpoint-postgres so /approve can
    #: land on any replica - requires POSTGRES_DSN and the [postgres-checkpoint]
    #: extra; falls back to memory with a warning if either is missing.
    checkpoint_backend: Literal["memory", "postgres"] = "memory"

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
