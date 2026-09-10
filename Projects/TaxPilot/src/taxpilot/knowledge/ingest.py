"""`tax-ingest` - build/inspect the IRS-rule index and check it against the catalog.

There is no vector database to populate (the BM25 index is built in memory at
startup), so ingest's real job is verification: parse the corpus, report what was
indexed, and fail loudly if a corpus file cites a rule_id the catalog does not
know - or if the catalog documents a rule no corpus file covers. That drift is
exactly what silently breaks the grounding guardrail, so it is worth a CLI.
"""

from __future__ import annotations

import argparse
import sys

from taxpilot.certs import enable_system_trust_store
from taxpilot.config import get_settings
from taxpilot.knowledge.corpus_loader import load_corpus
from taxpilot.knowledge.rules import RULES, is_known
from taxpilot.observability import setup_logging


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Index and verify the IRS-rule corpus.")
    parser.add_argument("--dry-run", action="store_true", help="parse only; print passage stats")
    args = parser.parse_args(argv)

    settings = get_settings()
    setup_logging(settings.log_level)
    enable_system_trust_store()

    corpus_dir = settings.absolute(settings.corpus_dir)
    if not corpus_dir.exists():
        print(f"Corpus directory not found: {corpus_dir}", file=sys.stderr)
        return 1

    passages = load_corpus(corpus_dir)
    print(f"{len(passages)} passages parsed from {corpus_dir}")
    if not passages:
        return 1

    lengths = sorted(len(p.text) for p in passages)
    print(f"  passage length: min={lengths[0]}  median={lengths[len(lengths) // 2]}  "
          f"max={lengths[-1]}")

    cited = {r for p in passages for r in p.rule_ids}
    unknown = sorted(r for r in cited if not is_known(r))
    uncovered = sorted(set(RULES) - cited)

    if unknown:
        print(f"\n!! corpus cites {len(unknown)} rule_id(s) absent from the catalog: {unknown}")
    if uncovered:
        print(f"\n   catalog rules with no corpus passage ({len(uncovered)}): {uncovered}")

    if args.dry_run:
        print("\nBy source:")
        for source in sorted({p.source for p in passages}):
            count = sum(1 for p in passages if p.source == source)
            print(f"  {source:<32} {count} passages")

    # Unknown citations are a hard error: they would make grounding checks lie.
    return 1 if unknown else 0


if __name__ == "__main__":
    sys.exit(main())
