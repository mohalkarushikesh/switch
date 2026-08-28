"""Retrieval metrics that need no LLM judge.

These are the metrics to tune on first: they are deterministic, cost nothing per
run, and every advanced retrieval layer in this project (hybrid fusion, HyDE,
reranking, CRAG rewriting) is supposed to move them.
"""

from __future__ import annotations

from dataclasses import dataclass

from advanced_rag.models import RetrievedChunk


@dataclass
class RetrievalScores:
    hit_rate: float
    recall: float
    mrr: float
    ndcg: float
    precision_at_k: float
    cases: int

    def as_row(self, label: str) -> dict[str, object]:
        return {
            "strategy": label,
            "hit@k": round(self.hit_rate, 3),
            "recall": round(self.recall, 3),
            "mrr": round(self.mrr, 3),
            "ndcg": round(self.ndcg, 3),
            "p@k": round(self.precision_at_k, 3),
            "cases": self.cases,
        }


def _sources(chunks: list[RetrievedChunk]) -> list[str]:
    return [hit.chunk.source for hit in chunks]


def hit_at_k(retrieved: list[RetrievedChunk], expected: list[str], k: int) -> float:
    """1.0 if any expected source appears in the top k."""
    found = set(_sources(retrieved[:k]))
    return 1.0 if found & set(expected) else 0.0


def recall_at_k(retrieved: list[RetrievedChunk], expected: list[str], k: int) -> float:
    """Fraction of the expected sources present in the top k."""
    if not expected:
        return 0.0
    found = set(_sources(retrieved[:k]))
    return len(found & set(expected)) / len(set(expected))


def reciprocal_rank(retrieved: list[RetrievedChunk], expected: list[str]) -> float:
    """1/rank of the first relevant result - rewards putting it first, not just present."""
    wanted = set(expected)
    for rank, source in enumerate(_sources(retrieved), start=1):
        if source in wanted:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved: list[RetrievedChunk], expected: list[str], k: int) -> float:
    """Binary-gain NDCG: discounts relevant hits that sit lower in the list.

    Labels are per *document*, but retrieval returns chunks and several chunks can
    share a source. Credit is therefore given once per source, at its best rank -
    otherwise a document that contributed four chunks scores 4x and NDCG exceeds
    1.0, which is meaningless.
    """
    import math

    wanted = set(expected)
    if not wanted:
        return 0.0

    gains: list[float] = []
    credited: set[str] = set()
    for source in _sources(retrieved[:k]):
        relevant = source in wanted and source not in credited
        if relevant:
            credited.add(source)
        gains.append(1.0 if relevant else 0.0)

    dcg = sum(gain / math.log2(index + 2) for index, gain in enumerate(gains))
    ideal_hits = min(len(wanted), k)
    idcg = sum(1.0 / math.log2(index + 2) for index in range(ideal_hits))
    return dcg / idcg if idcg else 0.0


def precision_at_k(retrieved: list[RetrievedChunk], expected: list[str], k: int) -> float:
    """Share of the top k that came from an expected source.

    Low precision with high recall is the signature of a retriever that needs
    reranking rather than better search.
    """
    window = _sources(retrieved[:k])
    if not window:
        return 0.0
    wanted = set(expected)
    return sum(1 for source in window if source in wanted) / len(window)


def score_all(
    results: list[tuple[list[RetrievedChunk], list[str]]], k: int = 5
) -> RetrievalScores:
    """Average every metric over (retrieved, expected) pairs."""
    scored = [(r, e) for r, e in results if e]
    if not scored:
        return RetrievalScores(0.0, 0.0, 0.0, 0.0, 0.0, 0)
    count = len(scored)
    return RetrievalScores(
        hit_rate=sum(hit_at_k(r, e, k) for r, e in scored) / count,
        recall=sum(recall_at_k(r, e, k) for r, e in scored) / count,
        mrr=sum(reciprocal_rank(r, e) for r, e in scored) / count,
        ndcg=sum(ndcg_at_k(r, e, k) for r, e in scored) / count,
        precision_at_k=sum(precision_at_k(r, e, k) for r, e in scored) / count,
        cases=count,
    )


def fact_coverage(answer: str, expected_facts: list[str]) -> float:
    """Share of expected substrings present in the answer, case-insensitively.

    Crude but useful: it catches an answer that talks around the question without
    ever naming the threshold, exit code or resource the runbook specifies.
    """
    if not expected_facts:
        return 1.0
    lowered = answer.lower()
    return sum(1 for fact in expected_facts if fact.lower() in lowered) / len(expected_facts)
