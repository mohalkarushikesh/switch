"""Approval agent: decide whether an invoice is auto-paid, reviewed, or rejected.

This is the policy layer in miniature — the routing rules that turn a risk
score into an action, using thresholds from configuration.
"""

from __future__ import annotations

from ..config import settings
from ..models import ApprovalDecision, Invoice, InvoiceStatus, RiskAssessment


class ApprovalAgent:
    def decide(self, invoice: Invoice, assessment: RiskAssessment) -> ApprovalDecision:
        """Route the invoice based on its risk score and amount."""
        score = assessment.risk_score

        # 1. Too risky → reject outright, no payment.
        if score >= settings.reject_min_risk:
            return ApprovalDecision(
                status=InvoiceStatus.REJECTED,
                reason=(
                    f"Risk score {score} >= reject threshold "
                    f"{settings.reject_min_risk}."
                ),
                requires_human=False,
            )

        # 2. Low risk AND within the amount cap → safe to auto-pay.
        if (
            score <= settings.auto_pay_max_risk
            and invoice.amount <= settings.auto_pay_max_amount
        ):
            return ApprovalDecision(
                status=InvoiceStatus.APPROVED,
                reason=(
                    f"Risk score {score} <= {settings.auto_pay_max_risk} and amount "
                    f"{invoice.amount} <= {settings.auto_pay_max_amount}."
                ),
                requires_human=False,
            )

        # 3. Everything in between → send to a human approver.
        return ApprovalDecision(
            status=InvoiceStatus.NEEDS_REVIEW,
            reason=(
                f"Risk score {score} or amount {invoice.amount} exceeds auto-pay "
                "limits; human review required."
            ),
            requires_human=True,
        )
