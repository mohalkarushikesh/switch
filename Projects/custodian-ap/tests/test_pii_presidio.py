"""Presidio PII backend tests — skipped unless presidio + the spaCy model exist.

The regex backend is covered in test_governance.py; this verifies the optional
Presidio backend produces the same backend-agnostic labels and redaction style.
"""

from __future__ import annotations

import pytest

# Skip the whole module if the optional dependencies aren't installed.
pytest.importorskip("presidio_analyzer")
spacy = pytest.importorskip("spacy")
if not spacy.util.is_package("en_core_web_sm"):
    pytest.skip("spaCy model en_core_web_sm not installed", allow_module_level=True)

from custodian.governance import data  # noqa: E402


@pytest.fixture(scope="module")
def redactor():
    # Force the Presidio backend regardless of CUSTODIAN_PII_BACKEND.
    return data.PIIRedactor(backend=data._PresidioBackend())


def test_presidio_backend_is_active(redactor):
    assert redactor.backend_name == "presidio"


def test_presidio_redacts_email_and_phone(redactor):
    redacted, found = redactor.redact_text(
        "Contact john.doe@example.com or call +1 415-555-0100 to confirm."
    )
    assert "EMAIL" in found
    assert "PHONE" in found
    assert "example.com" not in redacted
    assert "REDACTED" in redacted


def test_presidio_redacts_ssn(redactor):
    redacted, found = redactor.redact_text("SSN 123-45-6789 on file")
    assert "SSN" in found
    assert "123-45-6789" not in redacted
