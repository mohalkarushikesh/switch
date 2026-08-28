"""Data-governance layer: PII redaction with pluggable backends.

Scrubs personal / sensitive identifiers out of free-text invoice fields before
they are sent to an external LLM, so raw PII never leaves the trust boundary.

Two backends implement the same interface:
  - regex    : dependency-free pattern matcher (default; deterministic).
  - presidio : Microsoft Presidio's NLP-based analyzer (opt-in via
               CUSTODIAN_PII_BACKEND=presidio; requires presidio-analyzer +
               a spaCy model). Falls back to regex if unavailable.

Both emit the same short entity labels (EMAIL, PHONE, SSN, IBAN, CREDIT_CARD,
PERSON, ...) and the same "<LABEL_REDACTED>" replacement style, so the rest of
the system — and the tests — behave identically regardless of backend.
"""

from __future__ import annotations

import re

from ..config import settings
from ..models import Invoice

# --- Regex backend -----------------------------------------------------------

# Ordered so more specific patterns (SSN, IBAN) run before broad ones (numbers).
_PATTERNS: dict[str, re.Pattern] = {
    "EMAIL": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "IBAN": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d[ -]?){13,16}\b"),
    "PHONE": re.compile(r"\b\+?\d[\d\s().-]{7,}\d\b"),
}


class _RegexBackend:
    name = "regex"

    def redact_text(self, text: str | None) -> tuple[str, list[str]]:
        if not text:
            return text or "", []
        found: list[str] = []
        out = text
        for label, pattern in _PATTERNS.items():
            if pattern.search(out):
                found.append(label)
                out = pattern.sub(f"<{label}_REDACTED>", out)
        return out, found


# --- Presidio backend --------------------------------------------------------

# Map Presidio's entity types onto our short labels so output is backend-agnostic.
_PRESIDIO_LABELS: dict[str, str] = {
    "EMAIL_ADDRESS": "EMAIL",
    "PHONE_NUMBER": "PHONE",
    "US_SSN": "SSN",
    "IBAN_CODE": "IBAN",
    "CREDIT_CARD": "CREDIT_CARD",
    "PERSON": "PERSON",
    "LOCATION": "LOCATION",
    "US_BANK_NUMBER": "BANK_ACCOUNT",
}


class _PresidioBackend:
    name = "presidio"

    def __init__(self) -> None:
        # Imported lazily so the dependency is only needed when this backend is used.
        from presidio_analyzer import AnalyzerEngine
        from presidio_analyzer.nlp_engine import NlpEngineProvider

        # Use the small spaCy model to keep the footprint light.
        provider = NlpEngineProvider(nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        })
        self._analyzer = AnalyzerEngine(nlp_engine=provider.create_engine())

    @staticmethod
    def _drop_overlaps(results: list) -> list:
        """Keep the highest-scoring result among any overlapping spans."""
        chosen: list = []
        for r in sorted(results, key=lambda r: (r.start, -r.score)):
            if all(r.start >= c.end or r.end <= c.start for c in chosen):
                chosen.append(r)
        return chosen

    def redact_text(self, text: str | None) -> tuple[str, list[str]]:
        if not text:
            return text or "", []
        results = self._drop_overlaps(self._analyzer.analyze(text=text, language="en"))
        if not results:
            return text, []
        labels: set[str] = set()
        out = text
        # Replace spans back-to-front so earlier indices stay valid.
        for r in sorted(results, key=lambda r: r.start, reverse=True):
            label = _PRESIDIO_LABELS.get(r.entity_type, r.entity_type)
            labels.add(label)
            out = out[: r.start] + f"<{label}_REDACTED>" + out[r.end :]
        return out, sorted(labels)


def _make_backend(name: str):
    """Build the configured backend, falling back to regex if Presidio can't load."""
    if name in ("presidio", "auto"):
        try:
            return _PresidioBackend()
        except Exception:
            # Presidio or its model isn't available — degrade to regex.
            return _RegexBackend()
    return _RegexBackend()


# --- Public facade -----------------------------------------------------------


class PIIRedactor:
    def __init__(self, backend=None) -> None:
        self.backend = backend or _make_backend(settings.pii_backend)

    @property
    def backend_name(self) -> str:
        return self.backend.name

    def redact_text(self, text: str | None) -> tuple[str, list[str]]:
        """Return (redacted_text, entity_types_found) for a single string."""
        return self.backend.redact_text(text)

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
