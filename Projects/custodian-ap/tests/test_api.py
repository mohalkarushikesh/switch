"""Tests for the FastAPI service (heuristic path, no LLM needed)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Deterministic, offline scoring (conftest also sets CUSTODIAN_DISABLE_LLM).
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("GROQ_API_KEY", None)
os.environ.pop("HUGGINGFACE_API_KEY", None)
os.environ.pop("HF_TOKEN", None)

import pytest  # noqa: E402

fastapi_testclient = pytest.importorskip("fastapi.testclient")
from fastapi.testclient import TestClient  # noqa: E402

from custodian.api import app  # noqa: E402

client = TestClient(app)


def _clean_invoice(invoice_id: str = "API-001", amount: float = 1200.0) -> dict:
    return {
        "invoice_id": invoice_id,
        "vendor_name": "Acme Office Supplies",
        "vendor_account": "ACME-CHK-889201",
        "amount": amount,
        "currency": "INR",
        "issue_date": "2026-08-10",
        "due_date": "2026-09-10",
        "line_items": ["Paper", "Ink"],
        "memo": "Monthly order.",
    }


def test_health_reports_heuristic_mode():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["scoring_mode"] == "heuristic"
    # No provider is claimed when we're not actually calling an LLM, and the
    # dashboard is told the kill-switch is why.
    assert body["provider"] is None
    assert body["llm_disabled"] is True


def test_submit_clean_invoice_is_paid():
    resp = client.post("/invoices", json=_clean_invoice("API-PAID", 1500.0))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "paid"
    assert body["payment"]["paid"] is True
    assert body["assessment"]["source"] == "heuristic"


def test_submit_suspicious_invoice_is_rejected():
    payload = _clean_invoice("API-REJECT", 75000.0)
    payload.update(vendor_account="X12", line_items=[], memo="URGENT wire now")
    resp = client.post("/invoices", json=payload)
    assert resp.json()["status"] == "rejected"


def test_get_and_list_invoices():
    client.post("/invoices", json=_clean_invoice("API-LIST", 1000.0))
    # fetch one
    one = client.get("/invoices/API-LIST")
    assert one.status_code == 200
    assert one.json()["invoice"]["invoice_id"] == "API-LIST"
    # list all
    listing = client.get("/invoices")
    ids = {r["invoice"]["invoice_id"] for r in listing.json()}
    assert "API-LIST" in ids


def test_get_missing_invoice_returns_404():
    assert client.get("/invoices/does-not-exist").status_code == 404


def test_ledger_endpoint_reflects_payments():
    before = client.get("/ledger").json()["balance"]
    client.post("/invoices", json=_clean_invoice("API-LEDGER", 2000.0))
    after = client.get("/ledger").json()["balance"]
    assert after == before - 2000.0


def test_approve_review_invoice_triggers_payment():
    # A large invoice lands in needs_review; approving it pays it.
    client.post("/invoices", json=_clean_invoice("API-APPROVE", 48000.0))
    assert client.get("/invoices/API-APPROVE").json()["status"] == "needs_review"
    resp = client.post("/invoices/API-APPROVE/approve")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "paid"
    assert body["payment"]["paid"] is True


def test_reject_review_invoice():
    client.post("/invoices", json=_clean_invoice("API-REJ", 48000.0))
    resp = client.post("/invoices/API-REJ/reject")
    assert resp.json()["status"] == "rejected"


def test_cannot_approve_already_paid_invoice():
    client.post("/invoices", json=_clean_invoice("API-PAID2", 1000.0))  # auto-paid
    resp = client.post("/invoices/API-PAID2/approve")
    assert resp.status_code == 409


def test_delete_removes_invoice_and_refunds_ledger():
    # Pay a clean invoice, then delete it and confirm the ledger is refunded.
    client.post("/invoices", json=_clean_invoice("API-DEL", 1500.0))
    assert client.get("/invoices/API-DEL").json()["status"] == "paid"
    before = client.get("/ledger").json()["balance"]

    resp = client.delete("/invoices/API-DEL")
    assert resp.status_code == 200
    assert resp.json()["refunded"] == 1500.0

    assert client.get("/invoices/API-DEL").status_code == 404
    after = client.get("/ledger").json()["balance"]
    assert after == before + 1500.0


def test_delete_missing_invoice_is_404():
    assert client.delete("/invoices/does-not-exist").status_code == 404


def test_dashboard_is_served():
    resp = client.get("/ui/")
    assert resp.status_code == 200
    assert "Custodian" in resp.text


def test_batch_submit():
    payloads = [_clean_invoice("API-BATCH-1", 1000.0), _clean_invoice("API-BATCH-2", 2000.0)]
    resp = client.post("/invoices/batch", json=payloads)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_risk_range_filter():
    # 1234 is non-round, so no heuristic flags fire -> risk 0.
    client.post("/invoices", json=_clean_invoice("API-LOWRISK", 1234.0))
    resp = client.get("/invoices", params={"max_risk": 0})
    assert all(r["assessment"]["risk_score"] <= 0 for r in resp.json())
    assert any(r["invoice"]["invoice_id"] == "API-LOWRISK" for r in resp.json())


def test_stats_endpoint():
    resp = client.get("/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert "by_status" in body and "total_paid" in body
    assert body["total_invoices"] >= 1


def test_policies_endpoint():
    resp = client.get("/policies")
    assert resp.status_code == 200
    assert resp.json()["absolute_ceiling"] == 250000


def test_ocr_endpoint_processes_text():
    text = (
        "Invoice Number: OCR-API-1\n"
        "Vendor: Acme\n"
        "Account: ACME-CHK-889201\n"
        "Invoice Date: 2026-08-12\n"
        "Due Date: 2026-09-12\n"
        "- Paper\n"
        "Total: $1234.00\n"
    )
    resp = client.post("/invoices/ocr", json={"text": text})
    assert resp.status_code == 200
    body = resp.json()
    assert body["invoice"]["invoice_id"] == "OCR-API-1"
    assert body["status"] == "paid"


def test_ocr_endpoint_bad_text_is_422():
    resp = client.post("/invoices/ocr", json={"text": "nothing useful here"})
    assert resp.status_code == 422


def test_metrics_endpoint_prometheus_format():
    client.post("/invoices", json=_clean_invoice("API-METRICS", 1500.0))
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    assert "custodian_invoices_total" in body
    assert "custodian_ledger_balance" in body
    assert 'custodian_invoices_by_status{status="paid"}' in body


def test_audit_endpoint_returns_entries():
    # SQLite audit log is always on; submitting produces an audit entry.
    client.post("/invoices", json=_clean_invoice("API-AUDIT", 1500.0))
    resp = client.get("/audit")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["entries"]) >= 1
    assert any(e["invoice"]["invoice_id"] == "API-AUDIT" for e in body["entries"])


def test_audit_entries_carry_timestamps():
    """The audit view needs to show *when* each decision was recorded."""
    client.post("/invoices", json=_clean_invoice("API-AUDIT-TS", 1600.0))
    body = client.get("/audit").json()
    entry = next(e for e in body["entries"] if e["invoice"]["invoice_id"] == "API-AUDIT-TS")
    assert entry["recorded_at"]
    assert isinstance(entry["audit_id"], int)


def test_audit_limit_keeps_the_most_recent_events():
    for i in range(3):
        client.post("/invoices", json=_clean_invoice(f"API-AUDIT-LIM-{i}", 1700.0))
    full = client.get("/audit").json()
    limited = client.get("/audit?limit=2").json()

    assert len(limited["entries"]) == 2
    # total reports the full log size, not the truncated page.
    assert limited["total"] == full["total"] > 2
    # It's the tail that's kept (most recent), still in oldest-first order.
    assert [e["audit_id"] for e in limited["entries"]] == [
        e["audit_id"] for e in full["entries"][-2:]
    ]


def test_duplicate_submission_is_blocked_and_preserves_original():
    # First submission of a clean invoice is auto-paid.
    first = client.post("/invoices", json=_clean_invoice("API-DUP", 1234.0))
    assert first.json()["status"] == "paid"
    # Re-submitting the same id is blocked as a duplicate...
    second = client.post("/invoices", json=_clean_invoice("API-DUP", 1234.0))
    assert second.json()["status"] == "rejected"
    assert any(v["code"] == "duplicate_invoice" for v in second.json()["policy_violations"])
    # ...and the stored record still reflects the original paid state.
    assert client.get("/invoices/API-DUP").json()["status"] == "paid"


# NOTE: keep this LAST — it wipes the shared in-memory store/ledger.
def test_delete_all_clears_and_resets_ledger():
    client.post("/invoices", json=_clean_invoice("DA-1", 1000.0))
    client.post("/invoices", json=_clean_invoice("DA-2", 2000.0))
    assert len(client.get("/invoices").json()) >= 2

    resp = client.delete("/invoices")
    assert resp.status_code == 200
    assert resp.json()["deleted"] >= 2

    assert client.get("/invoices").json() == []
    assert client.get("/ledger").json()["balance"] == 1_000_000  # reset to start
