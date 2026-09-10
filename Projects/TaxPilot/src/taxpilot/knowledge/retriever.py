"""Retrieval over the IRS-rule corpus for the deduction researcher.

Thin layer on top of the BM25 store: builds the index once from the corpus
directory, runs one or several queries, deduplicates by passage, and renders a
numbered context block the researcher agent can cite by rule_id.
"""

from __future__ import annotations

import logging

from taxpilot.config import Settings, get_settings
from taxpilot.knowledge.corpus_loader import load_corpus
from taxpilot.knowledge.store import Bm25Store, Passage, ScoredPassage

logger = logging.getLogger(__name__)


class Retriever:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        corpus_dir = self.settings.absolute(self.settings.corpus_dir)
        passages = load_corpus(corpus_dir) if corpus_dir.exists() else []
        if not passages:
            logger.warning("No corpus passages found under %s", corpus_dir)
        self.store = Bm25Store(passages)

    def retrieve(self, query: str, *, top_k: int | None = None) -> list[ScoredPassage]:
        return self.store.search(query, top_k=top_k or self.settings.retrieve_top_k)

    def retrieve_multi(self, queries: list[str], *, top_k: int | None = None) -> list[Passage]:
        """Union of the top hits for several queries, best-score-first, deduped.

        The researcher issues one query per candidate topic (standard deduction,
        self-employment, child tax credit, ...); this merges them into a single
        context so a rule that ranks highly for two queries still appears once.
        """
        best: dict[str, ScoredPassage] = {}
        for query in queries:
            for hit in self.retrieve(query, top_k=top_k):
                current = best.get(hit.passage.id)
                if current is None or hit.score > current.score:
                    best[hit.passage.id] = hit
        ordered = sorted(best.values(), key=lambda s: s.score, reverse=True)
        return [s.passage for s in ordered]

    def count(self) -> int:
        return len(self.store)


def format_context(passages: list[Passage]) -> str:
    """Render passages as a numbered block that names each rule_id.

    The researcher is told to cite rule_ids, so they are printed prominently; the
    grounding guardrail later checks that whatever it cited actually appears here.
    """
    blocks = []
    for index, passage in enumerate(passages, start=1):
        rules = ", ".join(passage.rule_ids) if passage.rule_ids else "(none)"
        header = f"[{index}] {passage.source} - {passage.section}  (rule_ids: {rules})"
        blocks.append(header + "\n" + passage.text)
    return "\n\n".join(blocks)


_retriever: Retriever | None = None


def get_retriever() -> Retriever:
    global _retriever
    if _retriever is None:
        _retriever = Retriever()
    return _retriever


def reset_retriever() -> None:
    """Test hook - rebuild the index on next use (e.g. after pointing at a temp corpus)."""
    global _retriever
    _retriever = None
