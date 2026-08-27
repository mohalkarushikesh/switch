"""Tests for the governance layers: data (PII), policy, and audit log."""

from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("GROQ_API_KEY", None)

from custodian.governance import AuditLog, PIIRedactor, PolicyEngine  # noqa: E402
from custodian.ledger import Ledger  # noqa: E402
from custodian.models import Invoice, InvoiceStatus  # noqa: E402
from custodian.orchestrator import Custodian  # noqa: E402


def _invoice(**overrides) -> Invoice:
    base = dict(
        invoice_id="GOV-1",
        vendor_name="Test Vendor",
        vendor_account="TEST-CHK-123456",
        amount=1000.0,
        issue_date=date(2026, 8, 1),
        due_date=date(2026, 9, 1),
        line_items=["Consulting"],
        memo="Normal invoice.",
    )
    base.update(overrides)
    return Invoice(**base)


# --- Data layer / PII redaction ---

def test_pii_redactor_scrubs_email_and_phone():
    r = PIIRedactor()
    text = "Contact john.doe@example.com or call +1 415-555-0100 to confirm."
    redacted, found = r.redact_text(text)
    assert "EMAIL" in found and "PHONE" in found
    assert "example.com" not in redacted
    assert "REDACTED" in redacted


def test_redact_invoice_reports_entities_and_preserves_structure():
    r = PIIRedactor()
    inv = _invoice(memo="Reach me at jane@bank.com", line_items=["SSN 123-45-6789 on file"])
    redacted, found = r.redact_invoice(inv)
    assert "EMAIL" in found and "SSN" in found
    # Structural fields untouched.
    assert redacted.vendor_account == inv.vendor_account
    assert redacted.amount == inv.amount


def test_pipeline_records_redacted_pii():
    custodian = Custodian(Ledger(balance=1_000_000))
    record = custodian.process(_invoice(memo="email me: ops@vendor.com"))
    assert "EMAIL" in record.redacted_pii


# --- Policy layer ---

def test_policy_blocks_amount_over_ceiling():
    engine = PolicyEngine(max_amount=250_000)
    violations = engine.evaluate(_invoice(amount=300_000))
    assert any(v.code == "exceeds_absolute_ceiling" and v.severity == "block" for v in violations)


def test_policy_blocks_denylisted_vendor():
    engine = PolicyEngine(blocked_vendors=("evil corp",))
    violations = engine.evaluate(_invoice(vendor_name="Evil Corp"))
    assert any(v.code == "blocked_vendor" for v in violations)


def test_policy_block_forces_rejection_in_pipeline():
    # Over-ceiling amount is rejected even though such amounts would otherwise
    # only go to review.
    custodian = Custodian(Ledger(balance=100_000_000), policy=PolicyEngine(max_amount=250_000))
    record = custodian.process(_invoice(amount=500_000))
    assert record.status is InvoiceStatus.REJECTED
    assert record.payment.paid is False


def test_policy_flag_downgrades_autopay_to_review():
    # Small, low-risk invoice would auto-pay, but a weak account flags it to review.
    custodian = Custodian(Ledger(balance=1_000_000))
    record = custodian.process(_invoice(amount=500.0, vendor_account="AB1"))
    assert record.status is InvoiceStatus.NEEDS_REVIEW
    assert any(v.code == "weak_vendor_account" for v in record.policy_violations)


# --- Audit layer ---

def test_audit_log_persists_processed_invoices(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    custodian = Custodian(Ledger(balance=1_000_000), audit_log=AuditLog(log_path))
    custodian.process(_invoice(invoice_id="AUD-1", amount=1000.0))
    custodian.process(_invoice(invoice_id="AUD-2", amount=2000.0))

    entries = AuditLog(log_path).read_all()
    assert len(entries) == 2
    ids = {e["invoice"]["invoice_id"] for e in entries}
    assert ids == {"AUD-1", "AUD-2"}
    # Audit trail is persisted too.
    assert entries[0]["audit_trail"]
