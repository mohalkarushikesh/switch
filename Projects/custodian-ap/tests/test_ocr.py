"""Tests for OCR-text ingest (parse_invoice_text + IngestAgent.from_text)."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from custodian.agents import IngestAgent
from custodian.models import Invoice
from custodian.ocr import parse_invoice_text

_SAMPLE = """
ACME OFFICE SUPPLIES

Invoice Number: OCR-001
Vendor: Acme Office Supplies
Account: ACME-CHK-889201
Invoice Date: 2026-08-12
Due Date: 2026-09-12

Line items:
- Printer paper (20 boxes)
- Ink cartridges (12)

Total: $1,340.75
Memo: Monthly office supply order, PO-5521.
"""


def test_parse_extracts_all_fields():
    fields = parse_invoice_text(_SAMPLE)
    assert fields["invoice_id"] == "OCR-001"
    assert fields["vendor_name"] == "Acme Office Supplies"
    assert fields["vendor_account"] == "ACME-CHK-889201"
    assert fields["amount"] == 1340.75          # comma stripped, float
    assert fields["issue_date"] == "2026-08-12"
    assert fields["due_date"] == "2026-09-12"
    assert fields["line_items"] == ["Printer paper (20 boxes)", "Ink cartridges (12)"]
    assert "PO-5521" in fields["memo"]


def test_from_text_builds_valid_invoice():
    invoice = IngestAgent().from_text(_SAMPLE)
    assert isinstance(invoice, Invoice)
    assert invoice.invoice_id == "OCR-001"
    assert invoice.issue_date == date(2026, 8, 12)
    assert invoice.amount == 1340.75


def test_from_text_missing_required_field_raises():
    # No invoice id / vendor / amount / dates -> validation error.
    with pytest.raises(Exception):
        IngestAgent().from_text("Just some unrelated text with no fields.")


def test_bundled_sample_ocr_file_parses():
    sample = Path(__file__).resolve().parents[1] / "data" / "sample_ocr" / "invoice_ocr_1.txt"
    invoice = IngestAgent().from_text(sample.read_text(encoding="utf-8"))
    assert invoice.invoice_id == "OCR-001"
    assert invoice.amount == 1340.75
