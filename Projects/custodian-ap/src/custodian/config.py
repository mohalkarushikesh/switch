"""Central configuration, loaded once from environment variables (and .env)."""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()  # read a local .env file if present; no-op otherwise
except ImportError:  # dotenv is optional — env vars still work without it
    pass


def _get_int(name: str, default: int) -> int:
    """Read an int env var, falling back to the default if unset/invalid."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(float(raw))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    # LLM
    llm_model: str
    openai_api_key: str | None
    groq_api_key: str | None
    llm_api_base: str | None   # set to route through a LiteLLM proxy/gateway
    llm_api_key: str | None    # proxy master key (when using llm_api_base)

    # Approval-routing thresholds
    auto_pay_max_risk: int
    auto_pay_max_amount: int
    reject_min_risk: int

    # Mock ledger
    ledger_balance: int

    # Governance
    policy_max_amount: int          # absolute ceiling; any invoice above is blocked
    blocked_vendors: tuple[str, ...]  # denied vendor names (lower-cased)
    audit_log_path: str | None      # if set, processed invoices are appended here as JSONL

    # Persistence
    db_path: str                    # SQLite path; ":memory:" for ephemeral, a file for durable

    # PII redaction backend: "regex" (default, no deps), "presidio", or "auto"
    pii_backend: str

    # API auth: comma-separated "key:role" pairs (roles: submitter/reviewer/admin).
    # Empty = auth disabled (all endpoints open).
    api_keys: str

    # Notifications: fire on rejected or high-risk invoices.
    notify_min_risk: int             # risk score at/above which "high_risk" fires
    webhook_url: str | None          # POST notifications here (best-effort)
    notify_log_path: str | None      # append notifications to this JSONL file

    # Model tracking (governance "Model" layer): if set, each risk-scoring
    # decision is logged to MLflow (a local file store like "./mlruns", or a
    # tracking-server URL). Empty = disabled.
    mlflow_tracking_uri: str | None
    mlflow_experiment: str

    @property
    def has_llm_credentials(self) -> bool:
        """True if we can reach an LLM: a direct provider key or a proxy base URL."""
        return bool(self.openai_api_key or self.groq_api_key or self.llm_api_base)


def load_settings() -> Settings:
    """Build a Settings snapshot from the current environment."""
    return Settings(
        llm_model=os.getenv("CUSTODIAN_LLM_MODEL", "gpt-4o-mini"),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        groq_api_key=os.getenv("GROQ_API_KEY") or None,
        llm_api_base=os.getenv("CUSTODIAN_LLM_API_BASE") or None,
        llm_api_key=os.getenv("CUSTODIAN_LLM_API_KEY") or None,
        auto_pay_max_risk=_get_int("CUSTODIAN_AUTO_PAY_MAX_RISK", 30),
        auto_pay_max_amount=_get_int("CUSTODIAN_AUTO_PAY_MAX_AMOUNT", 5000),
        reject_min_risk=_get_int("CUSTODIAN_REJECT_MIN_RISK", 75),
        ledger_balance=_get_int("CUSTODIAN_LEDGER_BALANCE", 1_000_000),
        policy_max_amount=_get_int("CUSTODIAN_POLICY_MAX_AMOUNT", 250_000),
        blocked_vendors=tuple(
            v.strip().lower()
            for v in os.getenv("CUSTODIAN_BLOCKED_VENDORS", "").split(",")
            if v.strip()
        ),
        audit_log_path=os.getenv("CUSTODIAN_AUDIT_LOG") or None,
        db_path=os.getenv("CUSTODIAN_DB_PATH") or "data/custodian.db",
        pii_backend=(os.getenv("CUSTODIAN_PII_BACKEND") or "regex").lower(),
        api_keys=os.getenv("CUSTODIAN_API_KEYS", ""),
        notify_min_risk=_get_int("CUSTODIAN_NOTIFY_MIN_RISK", 70),
        webhook_url=os.getenv("CUSTODIAN_WEBHOOK_URL") or None,
        notify_log_path=os.getenv("CUSTODIAN_NOTIFY_LOG") or None,
        mlflow_tracking_uri=os.getenv("CUSTODIAN_MLFLOW_URI") or None,
        mlflow_experiment=os.getenv("CUSTODIAN_MLFLOW_EXPERIMENT", "custodian-risk"),
    )


# Module-level singleton used throughout the app
settings = load_settings()
