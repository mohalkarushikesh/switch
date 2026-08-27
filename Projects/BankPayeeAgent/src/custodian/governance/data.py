"""Data-governance layer: Presidio-style PII redaction.

Scrubs personal / sensitive identifiers out of free-text invoice fields before
they are sent to an external LLM, so raw PII never leaves the trust boundary.
Uses a lightweight regex detector here; in production this is where Microsoft
Presidio's analyzer/anonymizer would slot in behind the same interface.
"""

from __future__ import annotations

import re

from ..models import Invoice

# Ordered so more specific patterns (SSN, IBAN) run before broad ones (numbers).
_PATTERNS: dict[str, re.Pattern] = {
    "EMAIL": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "IBAN": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "PHONE": re.compile(r"\b\+?\d[\d\s().-]{7,}\d\b"),
}


class PIIRedactor:
    def redact_text(self, text: str | None) -> tuple[str, list[str]]:
        """Return (redacted_text, entity_types_found) for a single string."""
        if not text:
            return text or "", []
        found: list[str] = []
        out = text
        for label, pattern in _PATTERNS.items():
            if pattern.search(out):
                found.append(label)
                out = pattern.sub(f"<{label}_REDACTED>", out)
        return out, found

    def redact_invoice(self, invoice: Invoice) -> tuple[Invoice, list[str]]:
        """Return a redacted copy of the invoice plus the PII types scrubbed.

        Only free-text fields (memo, line items) are scrubbed; structural fields
        the pipeline needs (vendor name, account, amount) are left intact.
        """
        found: set[str] = set()

        memo, memo_hits = self.redact_text(invoice.memo)
        found.update(memo_hits)

        items: list[str] = []
        for item in invoice.line_items:
            redacted, hits = self.redact_text(item)
            items.append(redacted)
            found.update(hits)

        redacted_invoice = invoice.model_copy(
            update={"memo": memo or None, "line_items": items}
        )
        return redacted_invoice, sorted(found)
