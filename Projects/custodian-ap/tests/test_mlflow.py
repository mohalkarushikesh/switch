"""MLflow model-tracking tests — skipped unless mlflow is installed."""

from __future__ import annotations

from datetime import date

import pytest

pytest.importorskip("mlflow")

from custodian.ledger import Ledger  # noqa: E402
from custodian.models import Invoice  # noqa: E402
from custodian.orchestrator import Custodian  # noqa: E402
from custodian.tracking import build_tracker  # noqa: E402


def _invoice(invoice_id="ML-1", amount=1234.0) -> Invoice:
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


def test_scoring_is_logged_to_mlflow(tmp_path):
    # Use the client API (list of Run objects) to avoid the pandas dependency
    # that mlflow.search_runs pulls in (mlflow-skinny omits pandas).
    from mlflow.tracking import MlflowClient

    uri = (tmp_path / "mlruns").as_uri()
    tracker = build_tracker(uri, "custodian-test")
    assert tracker is not None

    cust = Custodian(Ledger(balance=1_000_000), tracker=tracker)
    rec = cust.process(_invoice("ML-1", 1234.0))
    assert any("MLflow" in step for step in rec.audit_trail)

    client = MlflowClient(tracking_uri=uri)
    exp = client.get_experiment_by_name("custodian-test")
    runs = client.search_runs([exp.experiment_id])
    assert len(runs) == 1
    run = runs[0]
    assert run.data.metrics["risk_score"] == rec.assessment.risk_score
    assert run.data.params["scoring_source"] == "heuristic"


def test_build_tracker_disabled_when_no_uri():
    assert build_tracker(None, "x") is None
