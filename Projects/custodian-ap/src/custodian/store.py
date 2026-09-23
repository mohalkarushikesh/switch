"""In-memory store for processed invoices.

A stand-in for the persistent ledger/audit database. Keeps the API stateless to
write against now, with a single place to swap in a real DB later.
"""

from __future__ import annotations

from .models import Invoice, ProcessedInvoice


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

    def known_vendor_accounts(self, vendor_name: str) -> set[str]:
        """Every payee account previously seen for this vendor (case-insensitive)."""
        key = vendor_name.strip().lower()
        return {
            r.invoice.vendor_account
            for r in self._records.values()
            if r.invoice.vendor_name.strip().lower() == key and r.invoice.vendor_account
        }

    def invoices_by_vendor(self, vendor_name: str) -> list[Invoice]:
        """Prior invoices for this vendor (case-insensitive) — near-dup candidates."""
        key = vendor_name.strip().lower()
        return [
            r.invoice for r in self._records.values()
            if r.invoice.vendor_name.strip().lower() == key
        ]
