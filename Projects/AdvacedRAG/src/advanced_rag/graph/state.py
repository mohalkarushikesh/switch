"""Graph state.

A TypedDict rather than a Pydantic model: LangGraph merges the dict a node
returns into this state, and `trace` uses an `operator.add` reducer so every node
can append its own step without reading what earlier nodes wrote.
"""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from advanced_rag.models import (
    Citation,
    GuardrailOutcome,
    RetrievedChunk,
    Route,
    SqlProposal,
    TraceStep,
    Verdict,
)


class RagState(TypedDict, total=False):
    # ---- input
    question: str
    #: The question as the user typed it, kept for citations and cache keys even
    #: after guardrail redaction or CRAG rewriting replaces `question`.
    original_question: str

    # ---- guardrails
    guardrails: Annotated[list[GuardrailOutcome], operator.add]
    blocked: bool
    block_message: str

    # ---- cache
    cached: bool
    cache_kind: str

    # ---- routing
    route: Route

    # ---- retrieval
    chunks: list[RetrievedChunk]
    context: str
    hyde_document: str | None
    retrieval_attempts: int

    # ---- CRAG
    verdict: Verdict
    verdict_reason: str
    rewrites: list[str]

    # ---- generation and Self-RAG
    answer: str
    critique: str
    self_rag_attempts: int
    #: Set when generation failed for an infrastructure reason (no credentials,
    #: network, rate limit). Such an answer must never be cached - otherwise a
    #: transient outage poisons the cache for the whole TTL.
    generation_failed: bool

    # ---- citations, carried explicitly so a cache hit can restore them
    citations: list[Citation]

    # ---- Text2SQL
    sql: SqlProposal | None
    sql_rows_text: str
    awaiting_approval: bool

    # ---- bookkeeping
    trace: Annotated[list[TraceStep], operator.add]
    input_tokens: int
    output_tokens: int


def initial_state(question: str) -> RagState:
    return RagState(
        question=question,
        original_question=question,
        guardrails=[],
        blocked=False,
        block_message="",
        cached=False,
        cache_kind="none",
        route=Route.VECTOR,
        chunks=[],
        context="",
        hyde_document=None,
        retrieval_attempts=0,
        verdict=Verdict.AMBIGUOUS,
        verdict_reason="",
        rewrites=[],
        answer="",
        critique="",
        self_rag_attempts=0,
        generation_failed=False,
        citations=[],
        sql=None,
        sql_rows_text="",
        awaiting_approval=False,
        trace=[],
        input_tokens=0,
        output_tokens=0,
    )

