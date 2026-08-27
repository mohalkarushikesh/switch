"""Tests for the SQLite persistence layer and duplicate detection."""

from __future__ import annotations

from datetime import date

from custodian.db import Database, SqliteAuditLog, SqliteStore
from custodian.ledger import Ledger
from custodian.models import Invoice, InvoiceStatus
from custodian.orchestrator import Custodian


def _invoice(invoice_id: str = "PER-1", amount: float = 1234.0) -> Invoice:
    return Invoice(
        invoice_id=invoice_id,
        vendor_name="Test Vendor",
        vendor_account="TEST-CHK-123456",
        amount=amount,
        issue_date=date(2026, 8, 1),
        due_date=date(2026, 9, 1),
        line_items=["Consulting"],
        memo="Normal invoice.",
    )


def test_store_roundtrip_and_status_filter():
    store = SqliteStore(Database(":memory:"))
    cust = Custodian(Ledger(balance=1_000_000))
    store.save(cust.process(_invoice("R-1", 1234.0)))       # paid
    store.save(cust.process(_invoice("R-2", 48000.0)))      # needs_review

    assert store.has("R-1") and not store.has("nope")
    assert store.get("R-1").status is InvoiceStatus.PAID
    assert len(store.list()) == 2
    assert {r.invoice.invoice_id for r in store.list(status="paid")} == {"R-1"}


def test_store_persists_across_restart(tmp_path):
    db_file = tmp_path / "custodian.db"

    # First "process": write with one connection, then drop it.
    store1 = SqliteStore(Database(db_file))
    cust = Custodian(Ledger(balance=1_000_000))
    store1.save(cust.process(_invoice("DUR-1", 1234.0)))

    # "Restart": a brand-new Database on the same file must see the record.
    store2 = SqliteStore(Database(db_file))
    got = store2.get("DUR-1")
    assert got is not None
    assert got.status is InvoiceStatus.PAID
    assert len(store2.list()) == 1


def test_duplicate_flag_blocks_second_processing():
    cust = Custodian(Ledger(balance=1_000_000))
    first = cust.process(_invoice("DUP-1", 1234.0), is_duplicate=False)
    assert first.status is InvoiceStatus.PAID

    second = cust.process(_invoice("DUP-1", 1234.0), is_duplicate=True)
    assert second.status is InvoiceStatus.REJECTED
    assert any(v.code == "duplicate_invoice" for v in second.policy_violations)


def test_process_many_flags_in_batch_duplicates():
    cust = Custodian(Ledger(balance=1_000_000))
    records = cust.process_many([_invoice("B-1", 1234.0), _invoice("B-1", 1234.0)])
    assert records[0].status is InvoiceStatus.PAID
    assert records[1].status is InvoiceStatus.REJECTED


def test_sqlite_audit_log_appends(tmp_path):
    db = Database(tmp_path / "audit.db")
    audit = SqliteAuditLog(db)
    cust = Custodian(Ledger(balance=1_000_000), audit_log=audit)
    cust.process(_invoice("AUD-1", 1234.0))
    cust.process(_invoice("AUD-2", 2345.0))

    entries = audit.read_all()
    assert len(entries) == 2
    assert {e["invoice"]["invoice_id"] for e in entries} == {"AUD-1", "AUD-2"}
