"""End-to-end smoke test: one folder of documents through the real pipeline.

Runs with no API key (deterministic extraction, classification and report) or with
one (the LLM agents engage). Use it after `tax-ingest` to confirm the whole stack
is wired up before pointing the web console at it.

    python scripts/smoke.py
    python scripts/smoke.py --approve      # auto-approve if the reviewer gate trips
"""

from __future__ import annotations

import argparse
import sys

from taxpilot.certs import enable_system_trust_store
from taxpilot.config import get_settings
from taxpilot.graph import pipeline
from taxpilot.models import ReturnResponse
from taxpilot.money import rupees
from taxpilot.observability import setup_logging


def show(response: ReturnResponse) -> None:
    ret = response.tax_return
    print("\n" + "=" * 78)
    if ret:
        verb = "refund" if ret.refund_or_due >= 0 else "payable"
        print(f"{ret.regime.value} regime  total income {rupees(ret.total_income)}  "
              f"tax {rupees(ret.total_tax)}  {verb} {rupees(abs(ret.refund_or_due))}")
        print(f"(other regime tax: {rupees(ret.alternative_regime_tax)})")
    print(f"latency={response.latency_ms}ms  tokens={response.input_tokens}->"
          f"{response.output_tokens}  awaiting_review={response.awaiting_review}")
    print("=" * 78)
    print(response.report)

    if response.audit:
        print(f"\nAudit risk: {response.audit.score}/100 ({response.audit.band})")
        for flag in response.audit.flags:
            print(f"  - {flag.code} ({flag.severity}, +{flag.weight}): {flag.detail}")

    skipped = [o for o in response.guardrails if o.action == "skip"]
    ran = len(response.guardrails) - len(skipped)
    print(f"\nGuardrails ({ran} of {len(response.guardrails)} ran):")
    for outcome in response.guardrails:
        mark = {"allow": "ok", "redact": "redacted", "annotate": "annotated",
                "block": "BLOCKED", "skip": "SKIPPED"}[outcome.action]
        print(f"  {outcome.layer:<18} {mark:<10} {outcome.detail}")
    if skipped:
        print(f"  !! failed open: {', '.join(o.layer for o in skipped)}")

    print("\nTrace:")
    for step in response.trace:
        print(f"  {step.node:<18} {step.elapsed_ms:>6} ms  {step.detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--approve", action="store_true",
                        help="auto-approve if the reviewer gate trips")
    args = parser.parse_args(argv)

    settings = get_settings()
    setup_logging(settings.log_level)
    enable_system_trust_store()

    directory = settings.absolute(settings.documents_dir)
    print(f"Preparing a return from {directory}")
    response = pipeline.prepare()
    show(response)

    if response.awaiting_review:
        print("\n--- awaiting human review ---")
        for item in response.review_items:
            print(f"  [{item.area}] {item.reason} {item.detail}")
        if not args.approve:
            print("\nRe-run with --approve to sign off and finish.")
            return 0
        print("\napproving with no corrections...")
        show(pipeline.resume(response.thread_id, corrections=[]))

    return 0


if __name__ == "__main__":
    sys.exit(main())
