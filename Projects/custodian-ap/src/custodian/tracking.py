"""Model-governance layer: track every risk-scoring decision in MLflow.

Answers "which model/version scored which invoice, and what did it decide?" —
each scoring becomes an MLflow run with params (invoice, model, scoring source)
and metrics (risk score, amount). Uses a local file store by default (no server
needed); set CUSTODIAN_MLFLOW_URI to "./mlruns" or a tracking-server URL.

Best-effort: a logging failure never breaks invoice processing.
"""

from __future__ import annotations

from .config import settings
from .models import Invoice, RiskAssessment


class ModelTracker:
    """Interface — implementations record a scoring event somewhere."""

    def log_scoring(self, invoice: Invoice, assessment: RiskAssessment) -> None:  # pragma: no cover
        raise NotImplementedError


class MlflowTracker(ModelTracker):
    def __init__(self, tracking_uri: str, experiment: str = "custodian-risk") -> None:
        import os

        # MLflow 3.x puts the local file store in "maintenance mode" and refuses
        # it unless this opt-in is set. The file store (e.g. ./mlruns) works fine
        # for this use; a SQLite/tracking-server URI needs no opt-in.
        os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")

        import mlflow  # imported lazily so mlflow is only needed when enabled

        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment)
        self._mlflow = mlflow

    def log_scoring(self, invoice: Invoice, assessment: RiskAssessment) -> None:
        mlflow = self._mlflow
        try:
            with mlflow.start_run(run_name=invoice.invoice_id):
                mlflow.log_params({
                    "invoice_id": invoice.invoice_id,
                    "vendor": invoice.vendor_name,
                    "model": settings.llm_model,
                    "scoring_source": assessment.source,   # "llm" or "heuristic"
                })
                mlflow.log_metrics({
                    "risk_score": assessment.risk_score,
                    "amount": invoice.amount,
                })
                mlflow.set_tags({
                    "fraud_flags": ", ".join(assessment.fraud_flags) or "none",
                    "currency": invoice.currency,
                })
        except Exception:
            # Tracking is observability, not correctness — never fail the pipeline.
            pass


def build_tracker(tracking_uri: str | None, experiment: str) -> ModelTracker | None:
    """Return an MlflowTracker if a URI is configured and mlflow imports, else None."""
    if not tracking_uri:
        return None
    try:
        return MlflowTracker(tracking_uri, experiment)
    except Exception:
        return None
