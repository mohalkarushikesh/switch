"""Near-duplicate invoice detection.

Exact re-submissions are caught by invoice-id (the `duplicate_invoice` block).
This catches the *evasive* case: the same invoice resubmitted with a tweaked id
(and maybe a nudged amount) to slip a second payment through — a common AP
double-payment / fraud vector.

Similarity is deliberately **explainable and model-free**: it compares the
structured fields a reviewer would compare by hand (amount, line items, memo,
issue date) and reports *why* two invoices look alike. That auditability matters
more here than an opaque embedding score, and it works offline with no deps. A
model-embedding backend could augment the text terms later without changing the
call site.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..models import Invoice

_WORD = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class NearDuplicate:
    """A prior invoice the incoming one closely resembles."""

    invoice_id: str   # the earlier invoice it matches
    score: float      # 0..1 composite similarity
    reason: str       # human-readable explanation for the audit trail


def _tokens(*parts: object) -> set[str]:
    """Lower-cased word/number tokens across the given text parts."""
    text = " ".join(str(p) for p in parts if p)
    return set(_WORD.findall(text.lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    """Set overlap in [0,1]; two empty sets count as a full match."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _amount_closeness(a: float, b: float) -> float:
    """1.0 when equal, decaying with relative difference (0 once it doubles)."""
    hi = max(abs(a), abs(b), 1.0)
    return max(0.0, 1.0 - abs(a - b) / hi)


def _date_closeness(a: Invoice, b: Invoice) -> float:
    days = abs((a.issue_date - b.issue_date).days)
    if days <= 2:
        return 1.0
    if days <= 7:
        return 0.7
    if days <= 30:
        return 0.4
    return 0.1


def _similarity(inv: Invoice, other: Invoice) -> tuple[float, str]:
    """Composite similarity of two same-vendor invoices, with an explanation.

    Amount closeness is a *multiplicative gate*, not just another weighted term: a
    double payment reuses (very close to) the same amount, so a large amount gap
    caps the score no matter how alike the text is. This is what separates an
    evasive re-submission from a legitimate repeat order that shares a line-item
    template but bills a different amount.
    """
    amount = _amount_closeness(inv.amount, other.amount)
    items = _jaccard(_tokens(*inv.line_items), _tokens(*other.line_items))
    memo = _jaccard(_tokens(inv.memo), _tokens(other.memo))
    text = 0.6 * items + 0.4 * memo
    date = _date_closeness(inv, other)

    content = 0.4 + 0.4 * text + 0.2 * date  # in [0.4, 1.0]
    score = amount * content
    same_amount = "same amount" if inv.amount == other.amount else f"{amount:.0%} amount match"
    reason = (
        f"{score:.0%} similar to invoice '{other.invoice_id}' "
        f"({same_amount}, {items:.0%} line-item overlap, "
        f"issued {abs((inv.issue_date - other.issue_date).days)}d apart)."
    )
    return score, reason


def find_near_duplicate(
    invoice: Invoice,
    candidates: list[Invoice],
    threshold: float = 0.85,
) -> NearDuplicate | None:
    """Return the most-similar prior invoice at/above `threshold`, else None.

    `candidates` should be prior invoices for the *same vendor* (the caller scopes
    by vendor). The incoming invoice's own id is skipped so an exact re-submission
    — already handled as a hard duplicate — doesn't also report as a near-duplicate.
    """
    best: NearDuplicate | None = None
    for other in candidates:
        if other.invoice_id == invoice.invoice_id:
            continue
        score, reason = _similarity(invoice, other)
        if score >= threshold and (best is None or score > best.score):
            best = NearDuplicate(invoice_id=other.invoice_id, score=round(score, 2), reason=reason)
    return best
