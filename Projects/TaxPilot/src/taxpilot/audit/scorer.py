"""Audit-risk scoring - a transparent heuristic layer.

Deliberately rule-based, not a learned model: there is no public training data for
the Income Tax Department's selection signal, and a preparer needs to see *why* a
return was flagged. Each flag carries its own weight and evidence; the score is
their capped sum; the band (with the amount threshold) drives whether the return
goes to a human.

The flags model well-known Indian red flags: TDS claimed in excess of Form 26AS,
Chapter VI-A deductions bunched at their statutory caps or unusually high relative
to income, large 80G donations, an HRA claim that needs proof, low-confidence
extractions, and a refund large relative to income.
"""

from __future__ import annotations

from taxpilot.models import (
    AuditRisk,
    DeductionCandidate,
    ExtractionResult,
    IncomeItem,
    RiskFlag,
    TaxReturn,
)
from taxpilot.money import rupees

_MEDIUM_AT = 40
_HIGH_AT = 70


def score_return(
    tax_return: TaxReturn,
    income: list[IncomeItem],
    deductions: list[DeductionCandidate],
    extractions: list[ExtractionResult] | None = None,
) -> AuditRisk:
    flags: list[RiskFlag] = []
    gti = max(1, tax_return.gross_total_income)

    _tds_vs_26as(flags, tax_return, extractions or [])
    _deductions_at_cap(flags, deductions)
    _chapter_via_ratio(flags, tax_return, gti)
    _large_donation(flags, deductions, gti)
    _needs_review(flags, deductions)
    _low_confidence(flags, extractions or [])
    _large_refund(flags, tax_return)

    score = min(100, sum(f.weight for f in flags))
    band = "high" if score >= _HIGH_AT else "medium" if score >= _MEDIUM_AT else "low"
    return AuditRisk(score=score, band=band, flags=flags)


# --------------------------------------------------------------------- checks


def _tds_vs_26as(
    flags: list[RiskFlag], ret: TaxReturn, extractions: list[ExtractionResult]
) -> None:
    """TDS claimed on the return must not exceed what Form 26AS reports."""
    statement = next((r for r in extractions if r.doc_type.value == "form26as"), None)
    if statement is None:
        return
    reported = int(round(statement.amount("tds")))
    if reported <= 0:
        return
    if ret.tds > reported + 1:
        flags.append(RiskFlag(
            code="tds_exceeds_26as", severity="high", weight=40,
            detail="TDS claimed is more than Form 26AS shows - refunds on the excess are held up.",
            evidence=f"claimed {rupees(ret.tds)} vs Form 26AS {rupees(reported)}",
        ))


def _deductions_at_cap(flags: list[RiskFlag], deductions: list[DeductionCandidate]) -> None:
    by_rule: dict[str, int] = {}
    for c in deductions:
        by_rule[c.citation.rule_id] = by_rule.get(c.citation.rule_id, 0) + c.amount
    caps = {"80C": 150_000, "80CCD1B": 50_000, "SEC24B": 200_000}
    maxed = [rid for rid, cap in caps.items() if by_rule.get(rid, 0) >= cap]
    if len(maxed) >= 2:
        flags.append(RiskFlag(
            code="deductions_at_cap", severity="medium", weight=12,
            detail="Several deductions are claimed at exactly their statutory ceiling.",
            evidence=", ".join(maxed),
        ))


def _chapter_via_ratio(flags: list[RiskFlag], ret: TaxReturn, gti: int) -> None:
    if ret.regime.value != "old" or ret.deductions_total <= 0:
        return
    ratio = ret.deductions_total / gti
    if ratio >= 0.4:
        flags.append(RiskFlag(
            code="high_deduction_ratio", severity="medium", weight=15,
            detail="Chapter VI-A deductions are a large share of gross total income.",
            evidence=f"deductions {rupees(ret.deductions_total)} = {ratio:.0%} of GTI",
        ))


def _large_donation(flags: list[RiskFlag], deductions: list[DeductionCandidate], gti: int) -> None:
    donation = sum(c.amount for c in deductions if c.citation.rule_id == "80G")
    if donation and donation / gti >= 0.1:
        flags.append(RiskFlag(
            code="large_80g_donation", severity="medium", weight=12,
            detail="Section 80G donation is large relative to income and invites scrutiny.",
            evidence=f"donation {rupees(donation)} is {donation / gti:.0%} of GTI",
        ))


def _needs_review(flags: list[RiskFlag], deductions: list[DeductionCandidate]) -> None:
    review = [c for c in deductions if c.needs_review]
    if review:
        flags.append(RiskFlag(
            code="deduction_needs_confirmation", severity="medium", weight=8 * min(len(review), 3),
            detail="Deductions whose eligibility depends on unconfirmed facts (e.g. HRA).",
            evidence=", ".join(c.name for c in review[:4]),
        ))


def _low_confidence(flags: list[RiskFlag], extractions: list[ExtractionResult]) -> None:
    weak = [f for r in extractions for f in r.fields if f.confidence < 0.6]
    if weak:
        flags.append(RiskFlag(
            code="low_confidence_extraction", severity="medium", weight=10 + min(10, len(weak) * 2),
            detail="Some figures were read from documents with low confidence.",
            evidence=", ".join(f"{f.name} ({f.confidence:.0%})" for f in weak[:4]),
        ))


def _large_refund(flags: list[RiskFlag], ret: TaxReturn) -> None:
    if ret.gross_total_income <= 0 or ret.refund_or_due <= 0:
        return
    if ret.refund_or_due / ret.gross_total_income >= 0.3:
        flags.append(RiskFlag(
            code="large_refund", severity="low", weight=8,
            detail="Refund is large relative to gross total income.",
            evidence=f"refund {rupees(ret.refund_or_due)} on GTI {rupees(ret.gross_total_income)}",
        ))
