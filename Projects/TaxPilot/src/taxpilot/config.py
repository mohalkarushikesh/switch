"""Central configuration.

Every external dependency is optional: no LLM key still runs the deterministic
engine and the BM25 knowledge base, no Tesseract still reads text documents, and
no network is ever required to compute or test a return. Blank/unset values
select the local fallback so the pipeline runs on a laptop with nothing installed
beyond the Python dependencies.
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
    #: Which backend the agents call through. "anthropic" = Claude via the
    #: Anthropic SDK; "gemini" = Google Gemini via google-genai.
    llm_provider: Literal["anthropic", "gemini"] = "anthropic"
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    llm_model: str = "claude-opus-4-8"
    #: Cheaper model for the many small extraction/classification/grading calls.
    llm_fast_model: str = "claude-haiku-4-5"
    llm_effort: str = "high"
    llm_max_tokens: int = 8_000
    llm_refusal_fallbacks: bool = True

    # ---------- Tax year ----------
    #: Financial-year start; 2024 == FY 2024-25 (AY 2025-26). The engine ships one
    #: year of constants at a time and errors loudly on any other year.
    tax_year: int = 2024

    # ---------- Knowledge base ----------
    corpus_dir: Path = Path("data/corpus")
    retrieve_top_k: int = 5

    # ---------- Document intake ----------
    documents_dir: Path = Path("data/documents")
    #: Below this confidence, an extracted field flags the return for human review.
    extraction_confidence_floor: float = Field(0.75, ge=0.0, le=1.0)

    # ---------- Reviewer gate ----------
    #: Audit-risk score (0-100) at or above which a human must sign off.
    review_risk_threshold: int = 60
    #: Refund or balance-payable magnitude (absolute rupees) that also forces review.
    review_amount_threshold: int = 100_000

    # ---------- Feature flags ----------
    enable_rag: bool = True
    enable_audit: bool = True
    enable_review: bool = True
    enable_guardrails: bool = True

    # ---------- Feedback ----------
    feedback_dir: Path = Path("feedback")

    # ---------- API ----------
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    log_level: str = "INFO"

    def absolute(self, path: Path) -> Path:
        """Resolve a configured path relative to the project root."""
        return path if path.is_absolute() else PROJECT_ROOT / path


@lru_cache
def get_settings() -> Settings:
    return Settings()
