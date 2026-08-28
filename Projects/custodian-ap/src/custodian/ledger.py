"""A mock ledger the auto-pay agent draws from.

Stands in for the real banking core / payment rail. It tracks a balance and
records every transaction so payments are traceable.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass
class Transaction:
    transaction_id: str
    invoice_id: str
    vendor_account: str
    amount: float
    currency: str


@dataclass
class Ledger:
    balance: float
    transactions: list[Transaction] = field(default_factory=list)

    def can_cover(self, amount: float) -> bool:
        """True if the current balance can fund this amount."""
        return amount <= self.balance

    def pay(self, invoice_id: str, vendor_account: str, amount: float,
            currency: str = "INR") -> Transaction:
        """Debit the balance and record the transaction.

        Raises ValueError if funds are insufficient — the caller is expected to
        check can_cover() first and handle the failure path.
        """
        if not self.can_cover(amount):
            raise ValueError(
                f"Insufficient funds: balance {self.balance} < amount {amount}"
            )
        self.balance -= amount
        txn = Transaction(
            transaction_id=f"TXN-{uuid.uuid4().hex[:12].upper()}",
            invoice_id=invoice_id,
            vendor_account=vendor_account,
            amount=amount,
            currency=currency,
        )
        self.transactions.append(txn)
        return txn

    def reverse(self, invoice_id: str) -> float:
        """Credit back and drop any transactions for an invoice; return the total.

        Used when a paid invoice is deleted, so the balance stays consistent with
        the set of stored invoices.
        """
        refunded = sum(t.amount for t in self.transactions if t.invoice_id == invoice_id)
        self.transactions = [t for t in self.transactions if t.invoice_id != invoice_id]
        self.balance += refunded
        return refunded
