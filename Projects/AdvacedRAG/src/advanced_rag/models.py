"""Shared data models used across ingestion, retrieval, the graph and the API."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """A retrievable unit of text plus its provenance."""

    id: str
    text: str
    source: str
    title: str = ""
    section: str = ""
    doc_type: str = "runbook"
    #: Free-form extras (k8s component, severity, version...) kept in the payload.
    metadata: dict[str, Any] = Field(default_factory=dict)

    def payload(self) -> dict[str, Any]:
        return {
            "chunk_id": self.id,
            "text": self.text,
            "source": self.source,
            "title": self.title,
            "section": self.section,
            "doc_type": self.doc_type,
            **self.metadata,
        }

    def citation(self) -> str:
        where = self.title or self.source
        return f"{where} - {self.section}" if self.section else where


class RetrievedChunk(BaseModel):
    """A chunk with the scores that got it here."""

    chunk: Chunk
    #: Fused retrieval score (RRF or weighted hybrid), higher is better.
    retrieval_score: float = 0.0
    #: Cross-encoder score after reranking, normalised to 0..1.
    rerank_score: float | None = None
    dense_rank: int | None = None
    sparse_rank: int | None = None

    @property
    def score(self) -> float:
        return self.rerank_score if self.rerank_score is not None else self.retrieval_score


class Route(StrEnum):
    """Where the router sends a question."""

    VECTOR = "vector"
    SQL = "sql"
    BOTH = "both"
    REJECT = "reject"


class Verdict(StrEnum):
    """CRAG's assessment of the retrieved context."""

    CORRECT = "correct"
    AMBIGUOUS = "ambiguous"
    INCORRECT = "incorrect"


class Citation(BaseModel):
    source: str
    title: str = ""
    section: str = ""
    score: float = 0.0


class SqlProposal(BaseModel):
    """A generated query awaiting human approval."""

    sql: str
    rationale: str = ""
    tables: list[str] = Field(default_factory=list)
    read_only: bool = True
    approved: bool = False
    #: Populated once executed.
    columns: list[str] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)
    row_count: int = 0
    error: str | None = None


class GuardrailOutcome(BaseModel):
    """Result of one guardrail layer.

    `passed` means the layer *ran* and cleared the content. A layer that could not
    run - an LLM classifier during an outage - reports `action="skip"` and
    `passed=False`: it did not block, but it also did not vet anything, and
    presenting that as a pass overstates the coverage the request actually got.
    """

    layer: str
    passed: bool
    action: Literal["allow", "redact", "block", "skip"] = "allow"
    detail: str = ""

    @property
    def ran(self) -> bool:
        return self.action != "skip"


class TraceStep(BaseModel):
    """One graph node execution, for the UI's pipeline view."""

    node: str
    detail: str = ""
    elapsed_ms: int = 0


class AnswerResponse(BaseModel):
    """What the API returns."""

    question: str
    answer: str
    route: Route = Route.VECTOR
    citations: list[Citation] = Field(default_factory=list)
    sql: SqlProposal | None = None
    #: True when the run stopped to ask for SQL approval.
    awaiting_approval: bool = False
    thread_id: str | None = None
    cached: bool = False
    cache_kind: Literal["none", "exact", "semantic"] = "none"
    guardrails: list[GuardrailOutcome] = Field(default_factory=list)
    blocked: bool = False
    trace: list[TraceStep] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
