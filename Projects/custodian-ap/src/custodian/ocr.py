"""OCR ingest: turn raw invoice text into structured fields.

This is the extraction half of the "Reader" stage. A real deployment feeds this
the text produced by an OCR engine (Tesseract) or a vision LLM; here we parse
that text with field heuristics. The output is handed to the Invoice model,
which enforces the required fields.
"""

from __future__ import annotations

import re

# Each canonical field maps to a regex whose first group captures the value.
# Patterns are anchored to the start of a line (re.MULTILINE) and require a
# ":"/"#" delimiter, so label-like substrings inside other words (e.g. "ac" in
# "ACME") can't spuriously match.
_FLAGS = re.IGNORECASE | re.MULTILINE
_LINE = r"^[ \t]*"
_FIELD_PATTERNS: dict[str, re.Pattern] = {
    "invoice_id": re.compile(
        _LINE + r"invoice\s*(?:id|no\.?|number|#)\s*[:#]\s*([A-Za-z0-9\-/]+)", _FLAGS),
    "vendor_name": re.compile(
        _LINE + r"(?:vendor|supplier|bill\s*from|from)\s*[:]\s*(.+)", _FLAGS),
    "vendor_account": re.compile(
        _LINE + r"(?:account|acct|iban|a/c)\s*(?:number|no\.?|#)?\s*[:#]\s*([A-Za-z0-9\-]+)", _FLAGS),
    "amount": re.compile(
        _LINE + r"(?:grand\s*total|amount\s*due|total|amount)\s*[:]\s*\$?\s*([\d,]+(?:\.\d{1,2})?)", _FLAGS),
    "issue_date": re.compile(
        _LINE + r"(?:invoice\s*date|issue\s*date|date)\s*[:]\s*(\d{4}-\d{2}-\d{2})", _FLAGS),
    "due_date": re.compile(
        _LINE + r"(?:due\s*date|payment\s*due|due)\s*[:]\s*(\d{4}-\d{2}-\d{2})", _FLAGS),
    "memo": re.compile(_LINE + r"(?:memo|notes?|description)\s*[:]\s*(.+)", _FLAGS),
}


def parse_invoice_text(text: str) -> dict:
    """Extract invoice fields from OCR-style text into a dict.

    Missing fields are simply omitted; the Invoice model decides which are
    required. Line items are read from bullet lines ("- ..." or "* ...").
    """
    fields: dict = {}
    for name, pattern in _FIELD_PATTERNS.items():
        match = pattern.search(text)
        if match:
            fields[name] = match.group(1).strip()

    # amount -> float (strip thousands separators)
    if "amount" in fields:
        try:
            fields["amount"] = float(fields["amount"].replace(",", ""))
        except ValueError:
            del fields["amount"]

    # line items from bullet lines
    items = [
        re.sub(r"^[-*]\s*", "", line).strip()
        for line in text.splitlines()
        if line.strip().startswith(("-", "*"))
    ]
    if items:
        fields["line_items"] = items

    return fields
