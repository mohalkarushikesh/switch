"""Tests for API-key authentication and role enforcement.

Auth is off by default (no keys configured); these tests enable it by patching
the app's key table, then restore it so other test modules stay unaffected.
"""

from __future__ import annotations

import pytest

from custodian.api import app
import custodian.api as api

from fastapi.testclient import TestClient

client = TestClient(app)

_KEYS = {"sk-sub": "submitter", "sk-rev": "reviewer", "sk-admin": "admin"}


@pytest.fixture()
def auth_enabled():
    """Enable auth for one test, then restore the original (disabled) state."""
    original = api._API_KEYS
    api._API_KEYS = dict(_KEYS)
    try:
        yield
    finally:
        api._API_KEYS = original


def _invoice(invoice_id: str, amount: float = 1234.0) -> dict:
    return {
        "invoice_id": invoice_id,
        "vendor_name": "Acme",
        "vendor_account": "ACME-CHK-889201",
        "amount": amount,
        "issue_date": "2026-08-10",
        "due_date": "2026-09-10",
        "line_items": ["x"],
        "memo": "ok",
    }


def test_submit_without_key_is_401(auth_enabled):
    resp = client.post("/invoices", json=_invoice("AUTH-1"))
    assert resp.status_code == 401


def test_submit_with_submitter_key_succeeds(auth_enabled):
    resp = client.post("/invoices", json=_invoice("AUTH-2"),
                        headers={"X-API-Key": "sk-sub"})
    assert resp.status_code == 200


def test_submitter_cannot_approve(auth_enabled):
    client.post("/invoices", json=_invoice("AUTH-3", 48000.0),
                headers={"X-API-Key": "sk-sub"})  # -> needs_review
    resp = client.post("/invoices/AUTH-3/approve", headers={"X-API-Key": "sk-sub"})
    assert resp.status_code == 403


def test_reviewer_can_approve(auth_enabled):
    client.post("/invoices", json=_invoice("AUTH-4", 48000.0),
                headers={"X-API-Key": "sk-sub"})
    resp = client.post("/invoices/AUTH-4/approve", headers={"X-API-Key": "sk-rev"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "paid"


def test_admin_can_do_anything(auth_enabled):
    assert client.post("/invoices", json=_invoice("AUTH-5"),
                       headers={"X-API-Key": "sk-admin"}).status_code == 200


def test_delete_requires_admin(auth_enabled):
    client.post("/invoices", json=_invoice("AUTH-DEL"), headers={"X-API-Key": "sk-sub"})
    # submitter and reviewer cannot delete
    assert client.delete("/invoices/AUTH-DEL", headers={"X-API-Key": "sk-sub"}).status_code == 403
    assert client.delete("/invoices/AUTH-DEL", headers={"X-API-Key": "sk-rev"}).status_code == 403
    # admin can
    assert client.delete("/invoices/AUTH-DEL", headers={"X-API-Key": "sk-admin"}).status_code == 200


# Reads that expose invoice or vendor data. /audit and /ledger return full
# invoice snapshots including vendor account numbers, so anonymous access to
# them would leak the entire AP history.
_PROTECTED_READS = ("/invoices", "/invoices/AUTH-READ", "/ledger", "/audit")

# Liveness and scrape endpoints stay open: /health is a probe, and Prometheus
# scrapes /metrics without credentials. Neither carries vendor data.
_OPEN_READS = ("/health", "/metrics")


@pytest.mark.parametrize("path", _PROTECTED_READS)
def test_sensitive_reads_require_a_key_when_auth_enabled(auth_enabled, path):
    assert client.get(path).status_code == 401


@pytest.mark.parametrize("path", _PROTECTED_READS)
def test_sensitive_reads_accept_any_valid_key(auth_enabled, path):
    # Seed the single-invoice path so it's a 200 rather than a 404.
    client.post("/invoices", json=_invoice("AUTH-READ"), headers={"X-API-Key": "sk-admin"})
    # Reads aren't role-scoped — the lowest-privilege key is enough.
    assert client.get(path, headers={"X-API-Key": "sk-sub"}).status_code == 200


@pytest.mark.parametrize("path", _OPEN_READS)
def test_probe_endpoints_stay_open_when_auth_enabled(auth_enabled, path):
    assert client.get(path).status_code == 200


@pytest.mark.parametrize("path", _PROTECTED_READS + _OPEN_READS)
def test_all_reads_open_when_auth_disabled(path):
    # No fixture -> _API_KEYS empty -> the local demo stays frictionless.
    client.post("/invoices", json=_invoice("AUTH-READ"))
    assert client.get(path).status_code == 200


def test_auth_disabled_by_default():
    # No fixture -> _API_KEYS empty -> writes allowed without a key.
    assert client.post("/invoices", json=_invoice("AUTH-OPEN")).status_code == 200
