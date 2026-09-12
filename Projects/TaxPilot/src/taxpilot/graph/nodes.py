"""Graph nodes - one per agent in the pipeline.

Each node is a plain function of state -> state patch with no knowledge of the
edges around it, so every stage is testable in isolation and the builder can
rewire the pipeline from feature flags. Every node that calls the model wraps the
call and falls back to a deterministic path, so the whole pipeline runs with no
API key - the calculate node never calls a model at all, by design.
"""

from __future__ import annotations

import logging
import re

from langgraph.types import interrupt
from pydantic import BaseModel, Field

from taxpilot.audit import score_return
from taxpilot.calc import compute
from taxpilot.config import get_settings
from taxpilot.extraction import Extractor, to_deductions, to_income
from taxpilot.graph.state import TaxState
from taxpilot.guardrails import get_guardrails
from taxpilot.knowledge import format_context, get_retriever, is_known
from taxpilot.llm import prompts
from taxpilot.llm.client import get_llm
from taxpilot.models import (
    AgeCategory,
    Correction,
    DeductionCandidate,
    DeductionKind,
    ReviewItem,
    TaxpayerProfile,
    TaxReturn,
)
from taxpilot.money import rupees
from taxpilot.observability import log_degraded, timed

logger = logging.getLogger(__name__)


def _maybe_llm(state: TaxState | None = None):
    """The shared client, or None to force the deterministic path.

    Returns None when the caller turned the LLM off for this run (`use_llm=False`)
    or when no client can be constructed (e.g. no API key). Either way every node
    that calls this simply takes its deterministic branch.
    """
    if state is not None and not state.get("use_llm", True):
        return None
    try:
        return get_llm()
    except Exception as exc:
        logger.warning("No LLM available (%s); running deterministic paths", type(exc).__name__)
        return None


# --------------------------------------------------------------- LLM schemas


class _ProfileOut(BaseModel):
    age_category: str = Field(description="below_60 | senior | super_senior")
    residential_status: str = Field(description="resident | non_resident")
    regime_preference: str = Field(description="old | new | auto")
    confidence: float = Field(description="0..1 confidence in the profile")
    reason: str


class _Proposal(BaseModel):
    name: str
    kind: str = Field(description="chapter_via | house_property | salary_exemption")
    amount: int = Field(description="rupee amount, or 0 if unknown")
    rule_id: str = Field(description="the rule_id from the retrieved context that authorises this")
    rationale: str
    needs_review: bool


class _Proposals(BaseModel):
    proposals: list[_Proposal]


# --------------------------------------------------------------------- nodes


def guardrail_intake_node(state: TaxState) -> dict:
    trace: list = []
    with timed(trace, "guardrail_intake") as step:
        result = get_guardrails().check_documents(
            state["documents"], use_llm=state.get("use_llm", True)
        )
        step.detail = f"{len(result.outcomes)} layers, blocked={result.blocked}"
    patch: dict = {"guardrails": result.outcomes, "trace": trace}
    if result.blocked:
        patch |= {"blocked": True, "block_message": result.message, "report": result.message}
    return patch


def extract_node(state: TaxState) -> dict:
    trace: list = []
    extractor = Extractor(llm=_maybe_llm(state))
    with timed(trace, "extract") as step:
        extractions = [extractor.extract(doc) for doc in state["documents"]]
        n_fields = sum(len(e.fields) for e in extractions)
        step.detail = f"{len(extractions)} documents, {n_fields} fields"
    return {"extractions": extractions, "trace": trace}


def classify_node(state: TaxState) -> dict:
    """Determine the age band and regime preference; normalize income deterministically."""
    trace: list = []
    review: list[ReviewItem] = []
    with timed(trace, "classify") as step:
        profile, confident = _classify_profile(state)
        override = state.get("regime_override")
        if override in ("old", "new", "auto"):
            profile = profile.model_copy(update={"regime_preference": override})
        income = to_income(state["extractions"])
        step.detail = (f"{profile.age_category.value}, regime={profile.regime_preference}, "
                       f"{len(income)} income items")
    if not confident:
        review.append(ReviewItem(
            reason="Age band / regime preference could not be confirmed from the documents.",
            area="extraction",
            detail=f"assumed {profile.age_category.value}, regime={profile.regime_preference}",
        ))
    return {"profile": profile, "income": income, "classify_notes": review, "trace": trace}


def research_node(state: TaxState) -> dict:
    """Deduction researcher (RAG). Proof documents normalize to grounded candidates
    deterministically; when RAG is on and a model is available it also proposes
    items from the retrieved sections, each of which must cite a retrieved rule_id."""
    settings = get_settings()
    trace: list = []
    candidates = to_deductions(state["extractions"])
    with timed(trace, "research") as step:
        if settings.enable_rag:
            llm = _maybe_llm(state)
            if llm is not None:
                candidates = _dedupe(candidates + _research_llm(llm, state, candidates))
        grounded = [c for c in candidates if c.grounded and is_known(c.citation.rule_id)]
        dropped = len(candidates) - len(grounded)
        step.detail = f"{len(grounded)} grounded deductions" + (
            f", {dropped} dropped as ungrounded" if dropped else "")
    return {"deductions": grounded, "trace": trace}


def calculate_node(state: TaxState) -> dict:
    """The deterministic engine (both regimes; keeps the cheaper). No model call."""
    settings = get_settings()
    trace: list = []
    with timed(trace, "calculate") as step:
        tax_return = compute(
            state["profile"], state["income"], state["deductions"], tax_year=settings.tax_year
        )
        verb = "refund" if tax_return.refund_or_due >= 0 else "payable"
        step.detail = (f"{tax_return.regime.value} regime, total income "
                       f"{rupees(tax_return.total_income)}, tax {rupees(tax_return.total_tax)}, "
                       f"{verb} {rupees(abs(tax_return.refund_or_due))}")
    return {"tax_return": tax_return, "trace": trace}


def audit_node(state: TaxState) -> dict:
    trace: list = []
    with timed(trace, "audit") as step:
        audit = score_return(
            state["tax_return"], state["income"], state["deductions"], state["extractions"]
        )
        step.detail = f"risk {audit.score}/100 ({audit.band}), {len(audit.flags)} flags"
    return {"audit": audit, "trace": trace}


def review_gate_node(state: TaxState) -> dict:
    """Escalate to a human when confidence is low, risk is high, or rupees are big."""
    settings = get_settings()
    trace: list = []
    tax_return = state.get("tax_return")
    items = _review_reasons(state, settings)
    required = bool(items)

    if not required or state.get("reviewed"):
        with timed(trace, "review_gate") as step:
            step.detail = "auto-approved" if not required else "already reviewed"
        return {"review_required": False, "review_items": items, "recompute": False,
                "trace": trace}

    decision = interrupt({
        "type": "return_review",
        "reasons": [i.model_dump() for i in items],
        "summary": {
            "regime": tax_return.regime.value if tax_return else "",
            "total_income": tax_return.total_income if tax_return else 0,
            "total_tax": tax_return.total_tax if tax_return else 0,
            "refund_or_due": tax_return.refund_or_due if tax_return else 0,
            "risk": state.get("audit").score if state.get("audit") else 0,
        },
    })
    corrections = _parse_corrections(decision)
    applied = _apply_corrections(state, corrections)
    with timed(trace, "review_gate") as step:
        step.detail = f"reviewed; {len(corrections)} correction(s)" + (
            "; recomputing" if applied else "")
    return {
        "reviewed": True, "review_required": True, "review_items": items,
        "corrections": corrections, "recompute": bool(applied), "trace": trace, **applied,
    }


def summarize_node(state: TaxState) -> dict:
    """Write the plain-language TL;DR before the review gate.

    Runs ahead of `review_gate` (and again on the correction-recompute pass) so the
    summary is committed to state and visible both while a return awaits human
    review and after approval - not only once the final report is written.
    """
    trace: list = []
    tax_return = state.get("tax_return")
    deductions = state.get("deductions") or []
    audit = state.get("audit")
    with timed(trace, "summarize") as step:
        llm = _maybe_llm(state)
        if llm is None or tax_return is None:
            step.detail = "no summary (deterministic run)"
            return {"trace": trace}
        summary = _llm_summary(llm, tax_return, deductions, audit)
        if summary is None:
            step.detail = "summary unavailable"
            return {"trace": trace}
        step.detail = f"LLM summary, {summary.output_tokens} output tokens"
        return {
            "llm_summary": summary.text,
            "input_tokens": state.get("input_tokens", 0) + summary.input_tokens,
            "output_tokens": state.get("output_tokens", 0) + summary.output_tokens,
            "trace": trace,
        }


def report_node(state: TaxState) -> dict:
    trace: list = []
    tax_return = state.get("tax_return")
    deductions = state.get("deductions") or []
    audit = state.get("audit")
    with timed(trace, "report") as step:
        deterministic = _deterministic_report(tax_return, deductions, audit)
        llm = _maybe_llm(state)
        if llm is None or tax_return is None:
            step.detail = "deterministic report"
            return {"report": deterministic, "trace": trace}
        try:
            result = llm.complete(_report_prompt(tax_return, deductions, audit),
                                  system=prompts.REPORTER_SYSTEM)
            if result.refused or not result.text:
                raise RuntimeError("empty or refused report")
            in_tok = state.get("input_tokens", 0) + result.input_tokens
            out_tok = state.get("output_tokens", 0) + result.output_tokens
            step.detail = f"LLM report, {out_tok} output tokens"
            return {"report": result.text, "input_tokens": in_tok,
                    "output_tokens": out_tok, "trace": trace}
        except Exception as exc:
            log_degraded(logger, "report", "Report generation failed, using template", exc)
            step.detail = "deterministic report (LLM failed)"
            return {"report": deterministic, "trace": trace}


def guardrail_output_node(state: TaxState) -> dict:
    trace: list = []
    with timed(trace, "guardrail_output") as step:
        result = get_guardrails().check_output(
            state.get("report", ""), state.get("tax_return"), state.get("deductions"),
            use_llm=state.get("use_llm", True),
        )
        step.detail = f"{len(result.outcomes)} layers, blocked={result.blocked}"
    patch: dict = {"guardrails": result.outcomes, "trace": trace}
    if result.blocked:
        patch |= {"blocked": True, "block_message": result.message, "report": result.message}
    else:
        patch["report"] = result.text
    return patch


def finalize_node(state: TaxState) -> dict:
    settings = get_settings()
    trace: list = []
    with timed(trace, "finalize") as step:
        corrections = state.get("corrections") or []
        if state.get("blocked") or not corrections:
            step.detail = "nothing to record"
            return {"trace": trace}
        _write_feedback(settings, state, corrections)
        step.detail = f"recorded {len(corrections)} correction(s)"
    return {"trace": trace}


# ------------------------------------------------------------- classify helpers


_AGE_SYNONYMS = {
    "below_60": AgeCategory.BELOW_60, "below 60": AgeCategory.BELOW_60,
    "senior": AgeCategory.SENIOR, "senior citizen": AgeCategory.SENIOR,
    "super_senior": AgeCategory.SUPER_SENIOR, "super senior": AgeCategory.SUPER_SENIOR,
}


def _to_age(text: str) -> AgeCategory | None:
    return _AGE_SYNONYMS.get(text.strip().lower())


def _to_regime_pref(text: str) -> str | None:
    value = text.strip().lower()
    return value if value in ("old", "new", "auto") else None


def _classify_profile(state: TaxState) -> tuple[TaxpayerProfile, bool]:
    llm = _maybe_llm(state)
    if llm is not None and get_settings().enable_rag:
        summary = "\n\n".join(f"[{d.doc_type.value}] {d.filename}\n{d.preview(500)}"
                              for d in state["documents"])
        try:
            out = llm.complete_json(summary, _ProfileOut, system=prompts.CLASSIFIER_SYSTEM)
            age = _to_age(out.age_category) or AgeCategory.BELOW_60
            regime = _to_regime_pref(out.regime_preference) or "auto"
            status = "non_resident" if "non" in out.residential_status.lower() else "resident"
            profile = TaxpayerProfile(age_category=age, residential_status=status,
                                      regime_preference=regime)
            return profile, out.confidence >= get_settings().extraction_confidence_floor
        except Exception as exc:
            log_degraded(logger, "classify", "LLM classification failed, parsing text", exc)
    return _parse_profile(state)


def _parse_profile(state: TaxState) -> tuple[TaxpayerProfile, bool]:
    text = "\n".join(d.text for d in state["documents"]).lower()
    age, regime, status, found = AgeCategory.BELOW_60, "auto", "resident", False

    match = re.search(r"age category\s*[:\-]\s*([a-z _]+)", text)
    if match and (parsed := _to_age(match.group(1))):
        age, found = parsed, True
    elif "super senior" in text:
        age, found = AgeCategory.SUPER_SENIOR, True
    elif "senior citizen" in text:
        age, found = AgeCategory.SENIOR, True

    match = re.search(r"(?:tax\s+)?regime\s*[:\-]\s*(old|new|auto)", text)
    if match:
        regime, found = match.group(1), True
    if "non-resident" in text or "non resident" in text:
        status, found = "non_resident", True

    return TaxpayerProfile(age_category=age, residential_status=status,
                           regime_preference=regime), found


# ------------------------------------------------------------- research helpers


def _research_llm(llm, state: TaxState, seed: list[DeductionCandidate]) -> list[DeductionCandidate]:
    passages = get_retriever().retrieve_multi(_research_queries(state))
    if not passages:
        return []
    allowed = {r for p in passages for r in p.rule_ids}
    seed_note = ", ".join(f"{c.name} ({rupees(c.amount)})" for c in seed) or "none"
    prompt = (f"Retrieved rules:\n{format_context(passages)}\n\n"
              f"Already-identified deductions from proofs: {seed_note}\n\n"
              f"Taxpayer: {state['profile'].age_category.value}, regime preference "
              f"{state['profile'].regime_preference}, {len(state['income'])} income items.\n\n"
              "Propose any additional deductions the rules support.")
    try:
        out = llm.complete_json(prompt, _Proposals, system=prompts.RESEARCHER_SYSTEM)
    except Exception as exc:
        log_degraded(logger, "research", "LLM research failed", exc)
        return []

    from taxpilot.knowledge.rules import cite
    proposals: list[DeductionCandidate] = []
    for item in out.proposals:
        grounded = is_known(item.rule_id) and item.rule_id in allowed
        if not grounded:
            logger.info("Dropping ungrounded proposal %s (rule_id=%s)", item.name, item.rule_id)
            continue
        try:
            kind = DeductionKind(item.kind)
        except ValueError:
            continue
        proposals.append(DeductionCandidate(
            name=item.name, kind=kind, amount=max(0, item.amount), citation=cite(item.rule_id),
            rationale=item.rationale, needs_review=item.needs_review, grounded=True,
        ))
    return proposals


def _research_queries(state: TaxState) -> list[str]:
    queries = [
        "standard deduction salary", "tax slabs new regime old regime", "rebate under section 87A",
        "section 80C investment deduction", "section 80D health insurance",
        "section 80CCD NPS deduction", "home loan interest section 24",
        "HRA house rent allowance exemption",
    ]
    for c in to_deductions(state["extractions"]):
        queries.append(c.name)
    return queries


def _dedupe(candidates: list[DeductionCandidate]) -> list[DeductionCandidate]:
    best: dict[tuple[str, str], DeductionCandidate] = {}
    for c in candidates:
        key = (c.citation.rule_id, c.kind.value)
        if key not in best or c.amount > best[key].amount:
            best[key] = c
    return list(best.values())


# --------------------------------------------------------------- review helpers


def _review_reasons(state: TaxState, settings) -> list[ReviewItem]:
    """Rebuilt fresh each call; seeds from classify_notes so the gate never
    re-appends its own reasons across a correction-recompute pass."""
    items: list[ReviewItem] = list(state.get("classify_notes") or [])

    for result in state.get("extractions") or []:
        weak = [f for f in result.fields if f.confidence < settings.extraction_confidence_floor]
        if weak:
            items.append(ReviewItem(
                reason="Low-confidence extracted fields.", area="extraction",
                detail=f"{result.doc_id}: " + ", ".join(f"{f.name} ({f.confidence:.0%})"
                                                         for f in weak[:4]),
            ))

    audit = state.get("audit")
    if audit and audit.score >= settings.review_risk_threshold:
        items.append(ReviewItem(
            reason=f"Audit risk {audit.score}/100 at or above the review threshold.",
            area="audit", detail="; ".join(f.code for f in audit.flags[:5]),
        ))

    tax_return = state.get("tax_return")
    if tax_return and abs(tax_return.refund_or_due) >= settings.review_amount_threshold:
        verb = "Refund" if tax_return.refund_or_due >= 0 else "Balance payable"
        items.append(ReviewItem(
            reason=f"{verb} of {rupees(abs(tax_return.refund_or_due))} at or above the "
                   f"{rupees(settings.review_amount_threshold)} threshold.",
            area="amount",
        ))

    for c in state.get("deductions") or []:
        if c.needs_review:
            items.append(ReviewItem(
                reason=f"Deduction '{c.name}' needs eligibility confirmation.",
                area="deduction", detail=c.citation.label(),
            ))
    return items


def _parse_corrections(decision) -> list[Correction]:
    raw = decision.get("corrections") if isinstance(decision, dict) else decision
    raw = raw or []
    corrections: list[Correction] = []
    for item in raw:
        if isinstance(item, Correction):
            corrections.append(item)
        elif isinstance(item, dict):
            corrections.append(Correction(**item))
    return corrections


def _apply_corrections(state: TaxState, corrections: list[Correction]) -> dict:
    patch: dict = {}
    profile = state["profile"]
    deductions = list(state.get("deductions") or [])
    changed = False
    for c in corrections:
        if c.target == "regime" and isinstance(c.value, str):
            pref = _to_regime_pref(c.value)
            if pref:
                profile = profile.model_copy(update={"regime_preference": pref})
                changed = True
        elif c.target == "age_category" and isinstance(c.value, str):
            age = _to_age(c.value)
            if age:
                profile = profile.model_copy(update={"age_category": age})
                changed = True
        elif c.target == "deduction_drop" and isinstance(c.value, str):
            before = len(deductions)
            deductions = [d for d in deductions if d.name.lower() != c.value.lower()]
            changed = changed or len(deductions) != before
    if changed:
        patch |= {"profile": profile, "deductions": deductions}
    return patch


def _write_feedback(settings, state: TaxState, corrections: list[Correction]) -> None:
    import json

    directory = settings.absolute(settings.feedback_dir)
    directory.mkdir(parents=True, exist_ok=True)
    record = {
        "documents": [d.filename for d in state["documents"]],
        "regime_preference": state["profile"].regime_preference,
        "corrections": [c.model_dump() for c in corrections],
    }
    with (directory / "corrections.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


# --------------------------------------------------------------- report helpers


def _report_prompt(tax_return: TaxReturn, deductions, audit) -> str:
    lines = "\n".join(f"- {line.label}: {rupees(line.amount)}"
                      + (f"  [{line.citation.label()}]" if line.citation else "")
                      for line in tax_return.lines)
    ded = "\n".join(f"- {c.name}: {rupees(c.amount)}  [{c.citation.label()}]"
                    for c in deductions) or "- none"
    flags = "\n".join(f"- {f.code} ({f.severity}): {f.detail}" for f in audit.flags) \
        if audit and audit.flags else "- none"
    verb = "refund" if tax_return.refund_or_due >= 0 else "balance payable"
    return (f"Chosen regime: {tax_return.regime.value}\n"
            f"Financial year: FY {tax_return.tax_year}-{(tax_return.tax_year + 1) % 100:02d}\n\n"
            f"Computed lines (use ONLY these figures):\n{lines}\n\n"
            f"Bottom line: {verb} of {rupees(abs(tax_return.refund_or_due))}\n"
            f"Tax under the other regime (for comparison): "
            f"{rupees(tax_return.alternative_regime_tax)}\n\n"
            f"Deductions applied:\n{ded}\n\n"
            f"Audit-risk flags (risk {audit.score if audit else 0}/100):\n{flags}\n\n"
            "Write the explanation now.")


def _summary_prompt(tax_return: TaxReturn, deductions, audit) -> str:
    verb = "refund" if tax_return.refund_or_due >= 0 else "balance payable"
    ded = ", ".join(f"{c.name} ({rupees(c.amount)})" for c in deductions) or "none"
    top_flag = audit.flags[0].detail if audit and audit.flags else "none"
    return (f"Regime chosen: {tax_return.regime.value} (tax under the other regime: "
            f"{rupees(tax_return.alternative_regime_tax)}).\n"
            f"Gross total income {rupees(tax_return.gross_total_income)}, taxable income "
            f"{rupees(tax_return.total_income)}, total tax {rupees(tax_return.total_tax)}.\n"
            f"Bottom line: {verb} of {rupees(abs(tax_return.refund_or_due))}.\n"
            f"Deductions applied: {ded}.\n"
            f"Audit risk: {audit.score if audit else 0}/100; top flag: {top_flag}.\n\n"
            "Write the 2-3 sentence summary now.")


def _llm_summary(llm, tax_return: TaxReturn, deductions, audit):
    """A short plain-language TL;DR, or None if the model declined, failed, or
    stated a rupee figure the engine did not compute (the same no-invented-numbers
    invariant the output guardrail enforces on the full report)."""
    try:
        result = llm.complete(
            _summary_prompt(tax_return, deductions, audit),
            system=prompts.SUMMARIZER_SYSTEM, max_tokens=400, thinking=False, effort="low",
        )
    except Exception as exc:
        log_degraded(logger, "report", "LLM summary failed", exc)
        return None
    if result.refused or not result.text:
        return None
    if _invents_figure(result.text, tax_return, deductions):
        logger.info("Dropping LLM summary: it stated a figure the engine did not compute")
        return None
    return result


def _invents_figure(text: str, tax_return: TaxReturn, deductions) -> bool:
    from taxpilot.guardrails import patterns
    from taxpilot.guardrails.pipeline import FIGURE_MIN, _CONSTANTS

    allowed = _CONSTANTS | tax_return.line_amounts() | {abs(c.amount) for c in (deductions or [])}
    return any(a >= FIGURE_MIN and a not in allowed for a in patterns.rupee_amounts(text))


def _deterministic_report(tax_return: TaxReturn | None, deductions, audit) -> str:
    if tax_return is None:
        return "No return was computed."
    fy = f"FY {tax_return.tax_year}-{(tax_return.tax_year + 1) % 100:02d}"
    verb = "Refund" if tax_return.refund_or_due >= 0 else "Balance payable"
    out = [f"# Draft {fy} Return - {tax_return.regime.value} regime", ""]
    out.append(f"Computed under the **{tax_return.regime.value} regime** (the lower-tax choice; "
               f"tax under the other regime would be {rupees(tax_return.alternative_regime_tax)}).")
    out += ["", "## Summary"]
    for line in tax_return.lines:
        if line.line == "alternative_regime_tax":
            continue
        cite = f"  _({line.citation.label()})_" if line.citation else ""
        out.append(f"- **{line.label}:** {rupees(line.amount)}{cite}")
    out += ["", f"**{verb}: {rupees(abs(tax_return.refund_or_due))}**"]
    if deductions:
        out += ["", "## Deductions applied"]
        for c in deductions:
            flag = " _(needs review)_" if c.needs_review else ""
            out.append(f"- {c.name}: {rupees(c.amount)} - {c.citation.label()}{flag}")
    if audit and audit.flags:
        out += ["", f"## Audit risk: {audit.score}/100 ({audit.band})"]
        for f in audit.flags:
            out.append(f"- **{f.code}** ({f.severity}): {f.detail}")
    out += ["", "_This is a draft return prepared for review by a qualified tax professional. "
            "It has not been filed and is not tax advice._"]
    return "\n".join(out)
