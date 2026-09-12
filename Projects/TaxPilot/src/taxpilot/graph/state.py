"""Graph state.

A TypedDict rather than a Pydantic model: LangGraph merges the dict each node
returns into this state, and the list fields that several nodes append to
(`guardrails`, `trace`) use an `operator.add` reducer so a node can add its own
entries without reading what earlier nodes wrote.
"""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from taxpilot.models import (
    AuditRisk,
    Correction,
    DeductionCandidate,
    ExtractionResult,
    GuardrailOutcome,
    IncomeItem,
    ReviewItem,
    SourceDocument,
    TaxpayerProfile,
    TaxReturn,
    TraceStep,
)


class TaxState(TypedDict, total=False):
    # ---- input
    documents: list[SourceDocument]

    # ---- extraction / classification
    extractions: list[ExtractionResult]
    profile: TaxpayerProfile
    income: list[IncomeItem]
    #: Force a regime ("old"/"new"/"auto") regardless of what the documents say -
    #: set by the caller to recompute the same return under the other regime.
    regime_override: str
    #: When False, every LLM-backed node skips the model and takes its deterministic
    #: path - the whole run is offline (no API key needed, faster, reproducible).
    use_llm: bool

    # ---- research (RAG)
    deductions: list[DeductionCandidate]

    # ---- deterministic computation
    tax_return: TaxReturn | None

    # ---- audit
    audit: AuditRisk | None

    # ---- reviewer gate
    review_required: bool
    #: Review notes raised by the classifier (e.g. unconfirmed filing status). Kept
    #: separate from `review_items` so the gate can recompute the full reason list
    #: fresh each pass without re-appending its own gate reasons (which would
    #: duplicate them across a correction-recompute loop).
    classify_notes: list[ReviewItem]
    review_items: list[ReviewItem]
    #: Set once a human has seen the return, so the gate interrupts at most once.
    reviewed: bool
    corrections: list[Correction]
    #: Routing flag: corrections changed an engine input, so recompute once. Kept
    #: separate from `corrections` (which finalize still needs) so clearing the
    #: route does not erase what the feedback log records.
    recompute: bool

    # ---- report
    report: str
    #: A short plain-language summary from the LLM; "" on a deterministic run.
    llm_summary: str

    # ---- guardrails
    guardrails: Annotated[list[GuardrailOutcome], operator.add]
    blocked: bool
    block_message: str

    # ---- bookkeeping
    trace: Annotated[list[TraceStep], operator.add]
    input_tokens: int
    output_tokens: int


def initial_state(
    documents: list[SourceDocument],
    regime_override: str = "",
    use_llm: bool = True,
) -> TaxState:
    return TaxState(
        documents=documents,
        extractions=[],
        profile=TaxpayerProfile(),
        income=[],
        regime_override=regime_override,
        use_llm=use_llm,
        deductions=[],
        tax_return=None,
        audit=None,
        review_required=False,
        classify_notes=[],
        review_items=[],
        reviewed=False,
        corrections=[],
        recompute=False,
        report="",
        llm_summary="",
        guardrails=[],
        blocked=False,
        block_message="",
        trace=[],
        input_tokens=0,
        output_tokens=0,
    )
