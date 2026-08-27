"""Payment agent: release funds for approved invoices via the mock ledger."""

from __future__ import annotations

from ..ledger import Ledger
from ..models import ApprovalDecision, Invoice, InvoiceStatus, PaymentResult


class PaymentAgent:
    def __init__(self, ledger: Ledger):
        self.ledger = ledger

    def pay(self, invoice: Invoice, decision: ApprovalDecision) -> PaymentResult:
        """Pay the invoice only if it was approved and funds are available."""
        # Guard: never pay anything that wasn't explicitly approved.
        if decision.status is not InvoiceStatus.APPROVED:
            return PaymentResult(
                paid=False,
                transaction_id=None,
                reason=f"Not approved for payment (status={decision.status.value}).",
            )

        # Guard: don't overdraw the ledger.
        if not self.ledger.can_cover(invoice.amount):
            return PaymentResult(
                paid=False,
                transaction_id=None,
                reason="Insufficient ledger balance.",
            )

        txn = self.ledger.pay(
            invoice_id=invoice.invoice_id,
            vendor_account=invoice.vendor_account,
            amount=invoice.amount,
            currency=invoice.currency,
        )
        return PaymentResult(
            paid=True,
            transaction_id=txn.transaction_id,
            reason=f"Paid {invoice.amount} {invoice.currency} to {invoice.vendor_account}.",
        )
