"""End-to-end tests for the Custodian pipeline (heuristic path, no LLM needed)."""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

# Make the src/ package importable without installing.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Ensure the LLM path is disabled so tests are deterministic and offline.
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("GROQ_API_KEY", None)

from custodian.ledger import Ledger  # noqa: E402
from custodian.models import Invoice, InvoiceStatus  # noqa: E402
from custodian.orchestrator import Custodian  # noqa: E402


def _invoice(**overrides) -> Invoice:
    base = dict(
        invoice_id="INV-TEST",
        vendor_name="Test Vendor",
        vendor_account="TEST-CHK-123456",
        amount=1000.0,
        currency="USD",
        issue_date=date(2026, 8, 1),
        due_date=date(2026, 9, 1),
        line_items=["Consulting"],
        memo="Normal invoice.",
    )
    base.update(overrides)
    return Invoice(**base)


def test_clean_small_invoice_is_auto_paid():
    custodian = Custodian(Ledger(balance=1_000_000))
    record = custodian.process(_invoice(amount=1200.0))
    assert record.status is InvoiceStatus.PAID
    assert record.payment.paid is True
    assert record.payment.transaction_id is not None
    # Ledger was debited.
    assert custodian.ledger.balance == 1_000_000 - 1200.0


def test_large_invoice_goes_to_review_and_is_not_paid():
    custodian = Custodian(Ledger(balance=1_000_000))
    record = custodian.process(_invoice(amount=48_250.0))
    assert record.status is InvoiceStatus.NEEDS_REVIEW
    assert record.payment.paid is False
    assert custodian.ledger.balance == 1_000_000  # untouched


def test_suspicious_invoice_is_rejected():
    custodian = Custodian(Ledger(balance=1_000_000))
    record = custodian.process(
        _invoice(
            amount=75_000.0,
            vendor_account="X12",           # too short
            line_items=[],                  # no line items
            memo="URGENT wire now immediately",
        )
    )
    assert record.status is InvoiceStatus.REJECTED
    assert record.payment.paid is False
    assert record.assessment.risk_score >= 75


def test_date_integrity_flag_raises_risk():
    custodian = Custodian(Ledger(balance=1_000_000))
    record = custodian.process(
        _invoice(amount=3000.0, issue_date=date(2026, 8, 20), due_date=date(2026, 8, 5))
    )
    assert "due date precedes issue date" in record.assessment.fraud_flags


def test_insufficient_funds_marks_failed():
    # Approve a small invoice but starve the ledger so payment fails.
    custodian = Custodian(Ledger(balance=100.0))
    record = custodian.process(_invoice(amount=1200.0))
    assert record.decision.status is InvoiceStatus.APPROVED
    assert record.status is InvoiceStatus.FAILED
    assert record.payment.paid is False


def test_audit_trail_is_populated():
    custodian = Custodian(Ledger(balance=1_000_000))
    record = custodian.process(_invoice())
    # Ingest + risk + approval + payment => at least 4 steps recorded.
    assert len(record.audit_trail) >= 4
