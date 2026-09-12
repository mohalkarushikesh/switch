"""Public entry point: run the pipeline and shape the result for callers.

Owns the human-in-the-loop protocol. `prepare()` may return with
`awaiting_review=True`, in which case the run is parked in the checkpointer under
`thread_id` and `resume()` continues it once a human has looked - optionally with
corrections that are recomputed deterministically.
"""

from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path
from typing import Any

from langgraph.types import Command

from taxpilot.config import get_settings
from taxpilot.graph.builder import get_graph
from taxpilot.graph.state import initial_state
from taxpilot.intake import load_documents
from taxpilot.models import (
    Citation,
    Correction,
    Regime,
    ReturnResponse,
    ReviewItem,
    SourceDocument,
    TraceStep,
)

logger = logging.getLogger(__name__)

#: LangGraph needs a recursion ceiling; the review loop is bounded to one extra
#: pass, so this only catches a genuine wiring mistake.
RECURSION_LIMIT = 30


def prepare(
    documents: list[SourceDocument] | None = None,
    *,
    documents_dir: str | Path | None = None,
    thread_id: str | None = None,
    regime: str | None = None,
    use_llm: bool = True,
    graph=None,
) -> ReturnResponse:
    """Prepare a draft return, pausing for review if the gate trips.

    `regime` ("old"/"new"/"auto") forces the regime regardless of the documents -
    used to recompute the same return under the other regime. `use_llm=False` runs
    the whole pipeline on its deterministic paths (no model call, no API key needed).
    """
    if documents is None:
        settings = get_settings()
        directory = Path(documents_dir) if documents_dir else settings.absolute(
            settings.documents_dir)
        documents = load_documents(directory)

    graph = graph or get_graph()
    thread_id = thread_id or uuid.uuid4().hex
    started = time.perf_counter()
    result = graph.invoke(
        initial_state(documents, regime or "", use_llm), config=_config(thread_id)
    )
    return _to_response(result, thread_id, started)


def resume(
    thread_id: str,
    *,
    corrections: list[Correction] | list[dict] | None = None,
    graph=None,
) -> ReturnResponse:
    """Continue a run parked at the reviewer gate."""
    graph = graph or get_graph()
    started = time.perf_counter()
    config = _config(thread_id)

    snapshot = graph.get_state(config)
    if not snapshot.values:
        raise KeyError(f"no run found for thread_id {thread_id!r}")

    payload = {"corrections": [_as_dict(c) for c in (corrections or [])]}
    result = graph.invoke(Command(resume=payload), config=config)
    return _to_response(result, thread_id, started)


def pending_review(thread_id: str, *, graph=None) -> dict[str, Any] | None:
    """The interrupt payload for a parked run, or None if nothing is pending."""
    graph = graph or get_graph()
    snapshot = graph.get_state(_config(thread_id))
    for task in snapshot.tasks or ():
        for pending in getattr(task, "interrupts", ()) or ():
            return dict(pending.value) if isinstance(pending.value, dict) else pending.value
    return None


def _config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}, "recursion_limit": RECURSION_LIMIT}


def _as_dict(correction: Correction | dict) -> dict:
    return correction.model_dump() if isinstance(correction, Correction) else correction


def _citations(result: dict[str, Any]) -> list[Citation]:
    """Unique citations behind the return, from engine lines and applied deductions."""
    seen: dict[str, Citation] = {}
    tax_return = result.get("tax_return")
    if tax_return is not None:
        for line in tax_return.lines:
            if line.citation:
                seen.setdefault(line.citation.rule_id, line.citation)
    for c in result.get("deductions") or []:
        seen.setdefault(c.citation.rule_id, c.citation)
    return list(seen.values())


def _to_response(result: dict[str, Any], thread_id: str, started: float) -> ReturnResponse:
    interrupts = result.get("__interrupt__") or ()
    awaiting = bool(interrupts)

    review_items = list(result.get("review_items") or [])
    if awaiting:
        # The gate's own patch never commits on the interrupting pass (interrupt()
        # raises first), so the committed review_items are only the classifier's
        # partial notes. The interrupt payload carries the full, authoritative
        # reason list - use it.
        payload = interrupts[0].value if isinstance(interrupts[0].value, dict) else {}
        if payload.get("reasons"):
            review_items = [ReviewItem(**r) for r in payload["reasons"]]

    tax_return = result.get("tax_return")
    trace = list(result.get("trace") or [])
    if awaiting:
        trace.append(TraceStep(node="review_gate", detail="awaiting human review"))

    settings = get_settings()
    return ReturnResponse(
        tax_year=settings.tax_year,
        regime=tax_return.regime if tax_return else Regime.NEW,
        tax_return=tax_return,
        audit=result.get("audit"),
        report=result.get("report", ""),
        llm_summary=result.get("llm_summary", ""),
        used_llm=bool(result.get("use_llm", True)),
        citations=_citations(result),
        awaiting_review=awaiting,
        review_items=review_items,
        thread_id=thread_id,
        guardrails=list(result.get("guardrails") or []),
        blocked=bool(result.get("blocked")),
        block_message=result.get("block_message", ""),
        trace=trace,
        input_tokens=int(result.get("input_tokens", 0)),
        output_tokens=int(result.get("output_tokens", 0)),
        latency_ms=int((time.perf_counter() - started) * 1000),
    )
