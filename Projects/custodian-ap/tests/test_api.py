"""Tests for the FastAPI service (heuristic path, no LLM needed)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Deterministic, offline scoring.
os.environ.pop("OPENAI_API_KEY", None)
os.environ.pop("GROQ_API_KEY", None)

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
        "currency": "USD",
        "issue_date": "2026-08-10",
        "due_date": "2026-09-10",
        "line_items": ["Paper", "Ink"],
        "memo": "Monthly order.",
    }


def test_health_reports_heuristic_mode():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["scoring_mode"] == "heuristic"


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
