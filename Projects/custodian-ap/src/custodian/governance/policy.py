"""Policy-governance layer: hard business rules layered over risk scoring.

Risk scoring is probabilistic; policy is deterministic and non-negotiable. A
"block" violation forces rejection regardless of how safe the risk score looked;
a "flag" violation forces human review of an otherwise auto-payable invoice.
"""

from __future__ import annotations

from ..config import settings
from ..models import Invoice, PolicyViolation
from .dedup import NearDuplicate


class PolicyEngine:
    def __init__(
        self,
        max_amount: int | None = None,
        blocked_vendors: tuple[str, ...] | None = None,
    ) -> None:
        self.max_amount = max_amount if max_amount is not None else settings.policy_max_amount
        # Store lower-cased for case-insensitive matching.
        self.blocked_vendors = {
            v.lower() for v in (blocked_vendors if blocked_vendors is not None else settings.blocked_vendors)
        }

    def evaluate(
        self,
        invoice: Invoice,
        is_duplicate: bool = False,
        account_changed: bool = False,
        near_duplicate: NearDuplicate | None = None,
    ) -> list[PolicyViolation]:
        """Return all policy violations for an invoice (empty list = compliant).

        is_duplicate signals that an invoice with this id was already processed —
        a classic double-payment vector, so it is blocked outright.

        account_changed signals that this vendor has been paid before but the
        payee account differs from every account seen previously — the classic
        BEC / vendor-impersonation vector. It is *flagged* (not blocked): a
        genuine bank-detail change happens, so a human must verify with the
        vendor out-of-band before releasing payment.

        near_duplicate, if set, is a prior invoice this one closely resembles
        (same vendor, near-identical fields) despite a different id — an evasive
        double-payment attempt. Flagged for human confirmation.
        """
        violations: list[PolicyViolation] = []

        # Near-duplicate of an earlier invoice — confirm it isn't a double payment.
        if near_duplicate is not None:
            violations.append(PolicyViolation(
                code="possible_duplicate",
                severity="flag",
                message=(
                    f"Resembles already-processed invoice "
                    f"'{near_duplicate.invoice_id}' — {near_duplicate.reason} "
                    f"Confirm this is not a double payment before releasing funds."
                ),
            ))

        # Vendor bank-account change — verify out-of-band before paying.
        if account_changed:
            violations.append(PolicyViolation(
                code="vendor_account_changed",
                severity="flag",
                message=(
                    f"Vendor '{invoice.vendor_name}' was paid before, but the payee "
                    f"account '{invoice.vendor_account}' is new. Confirm the change "
                    f"with the vendor through a known contact before paying."
                ),
            ))

        # Duplicate submission: never pay the same invoice twice.
        if is_duplicate:
            violations.append(PolicyViolation(
                code="duplicate_invoice",
                severity="block",
                message=f"Invoice id '{invoice.invoice_id}' was already processed.",
            ))

        # Data-integrity: a non-positive amount is never payable.
        if invoice.amount <= 0:
            violations.append(PolicyViolation(
                code="non_positive_amount",
                severity="block",
                message=f"Amount must be positive (was {invoice.amount}).",
            ))

        # Absolute spending ceiling — no single invoice may exceed it automatically.
        if invoice.amount > self.max_amount:
            violations.append(PolicyViolation(
                code="exceeds_absolute_ceiling",
                severity="block",
                message=f"Amount {invoice.amount} exceeds absolute ceiling {self.max_amount}.",
            ))

        # Denylisted vendor.
        if invoice.vendor_name.strip().lower() in self.blocked_vendors:
            violations.append(PolicyViolation(
                code="blocked_vendor",
                severity="block",
                message=f"Vendor '{invoice.vendor_name}' is on the deny list.",
            ))

        # Weak / malformed destination account — allow, but require human review.
        if not invoice.vendor_account or len(invoice.vendor_account) < 6:
            violations.append(PolicyViolation(
                code="weak_vendor_account",
                severity="flag",
                message="Vendor account is missing or too short; manual verification required.",
            ))

        return violations
