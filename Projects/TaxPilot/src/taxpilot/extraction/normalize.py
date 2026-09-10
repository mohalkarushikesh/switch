"""Deterministic normalization: extracted fields -> engine inputs.

Turning a Form 16 into a salary IncomeItem, or an 80C proof into a Chapter VI-A
DeductionCandidate, is settled structure - done here in plain code. The classifier
agent decides only what genuinely needs reading (age band, regime choice); the
deduction researcher decides eligibility and grounding.
"""

from __future__ import annotations

from taxpilot.calc.engine import whole_rupee
from taxpilot.extraction.schema import DEDUCTION_DOCS, INCOME_MAP
from taxpilot.knowledge.rules import cite
from taxpilot.models import Citation, DeductionCandidate, ExtractionResult, IncomeItem


def to_income(extractions: list[ExtractionResult]) -> list[IncomeItem]:
    """Build normalized income items (and carry TDS) from Form 16 / 16A / interest."""
    items: list[IncomeItem] = []
    for result in extractions:
        mapping = INCOME_MAP.get(result.doc_type)
        if not mapping:
            continue
        payer = result.field("payer")
        payer_name = payer.value if payer and isinstance(payer.value, str) else ""
        tds = whole_rupee(result.amount(mapping["withholding"]))
        primary_field = mapping["income"][0][0] if mapping["income"] else None
        primary_emitted = False
        for field_name, kind in mapping["income"]:
            amount = result.amount(field_name)
            if amount <= 0:
                continue
            is_primary = field_name == primary_field
            items.append(IncomeItem(
                kind=kind, amount=whole_rupee(amount), payer=payer_name,
                source_doc=result.doc_id, withholding=tds if is_primary else 0,
            ))
            primary_emitted = primary_emitted or is_primary
        if tds and not primary_emitted:
            # TDS with no income line of its own (Form 16A) still counts as a payment.
            items.append(IncomeItem(
                kind="other", amount=0, payer=payer_name, source_doc=result.doc_id,
                withholding=tds,
            ))
    return items


def to_deductions(extractions: list[ExtractionResult]) -> list[DeductionCandidate]:
    """Build deduction candidates from proof documents, grounded via the catalog."""
    candidates: list[DeductionCandidate] = []
    for result in extractions:
        rule = DEDUCTION_DOCS.get(result.doc_type)
        if rule is None:
            continue
        rule_id, kind, name, needs_review, amount_field = rule
        amount = whole_rupee(result.amount(amount_field))
        if amount <= 0:
            continue
        citation: Citation = cite(rule_id)
        candidates.append(DeductionCandidate(
            name=name, kind=kind, amount=amount, citation=citation,
            rationale=f"From {result.doc_type.value} document {result.doc_id}.",
            confidence=1.0, needs_review=needs_review, grounded=True,
        ))
    return candidates
