"""Policy-governance layer: hard business rules layered over risk scoring.

Risk scoring is probabilistic; policy is deterministic and non-negotiable. A
"block" violation forces rejection regardless of how safe the risk score looked;
a "flag" violation forces human review of an otherwise auto-payable invoice.
"""

from __future__ import annotations

from ..config import settings
from ..models import Invoice, PolicyViolation


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

    def evaluate(self, invoice: Invoice) -> list[PolicyViolation]:
        """Return all policy violations for an invoice (empty list = compliant)."""
        violations: list[PolicyViolation] = []

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
