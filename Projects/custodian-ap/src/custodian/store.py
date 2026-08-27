"""In-memory store for processed invoices.

A stand-in for the persistent ledger/audit database. Keeps the API stateless to
write against now, with a single place to swap in a real DB later.
"""

from __future__ import annotations

from .models import ProcessedInvoice


class InvoiceStore:
    def __init__(self) -> None:
        self._records: dict[str, ProcessedInvoice] = {}

    def save(self, record: ProcessedInvoice) -> None:
        """Insert or replace a processed invoice, keyed by invoice id."""
        self._records[record.invoice.invoice_id] = record

    def get(self, invoice_id: str) -> ProcessedInvoice | None:
        return self._records.get(invoice_id)

    def list(self, status: str | None = None) -> list[ProcessedInvoice]:
        """Return all records, optionally filtered by status value."""
        records = list(self._records.values())
        if status:
            records = [r for r in records if r.status.value == status]
        return records
