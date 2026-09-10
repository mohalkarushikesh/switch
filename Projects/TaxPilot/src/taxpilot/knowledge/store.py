"""Pure-Python BM25 index over the IRS-rule corpus.

Deliberately downloads nothing. The deduction researcher needs to retrieve the
right rule, not the semantically nearest sentence, and the corpus is a small
hand-curated set of publication excerpts - so a proper corpus-level BM25 (real
IDF from the documents, length normalisation) both fits the problem and runs on a
network that blocks huggingface.co. A dense/embedding arm could slot in behind the
same `Retriever` interface later; nothing above this module assumes lexical.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from pydantic import BaseModel, Field

#: BM25 term-frequency saturation and length-normalisation strength (standard).
K1 = 1.5
B = 0.75

_TOKEN = re.compile(r"[a-z0-9]+")

#: Small on purpose. Tax text leans on words a broad stoplist would drop -
#: "over", "under", "not", "self" ("self-employment") all carry meaning here.
_STOPWORDS = frozenset(
    """
    a an the and or but if then of in on at to for from by with as is are was were
    be been being this that these those it its they them their you your we our i
    """.split()
)


def tokenize(text: str) -> list[str]:
    """Lowercase, split on non-alphanumerics, drop stopwords, light plural stem."""
    tokens: list[str] = []
    for raw in _TOKEN.findall(text.lower()):
        if raw in _STOPWORDS:
            continue
        tokens.append(_stem(raw))
    return tokens


def _stem(token: str) -> str:
    """Fold a handful of plural/possessive suffixes so "deductions" == "deduction".

    Intentionally minimal: applied identically to documents and queries, so a
    crude-but-consistent rule beats an aggressive one that mangles "expenses" into
    something a query never reproduces.
    """
    if len(token) <= 4 or not token.isalpha():
        return token
    for suffix in ("ies", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 3:
            return token[: -len(suffix)] + ("y" if suffix == "ies" else "")
    return token


class Passage(BaseModel):
    """One retrievable chunk of a corpus document plus its provenance."""

    id: str
    text: str
    source: str = ""       # e.g. "IRS Pub 501"
    section: str = ""      # heading within the document
    rule_ids: list[str] = Field(default_factory=list)


class ScoredPassage(BaseModel):
    passage: Passage
    score: float


class Bm25Store:
    """An in-memory BM25 index. Built once from the corpus, queried per return."""

    def __init__(self, passages: list[Passage]) -> None:
        self.passages = passages
        self._tokens = [tokenize(p.text + " " + p.section) for p in passages]
        self._lengths = [len(t) for t in self._tokens]
        self._avgdl = (sum(self._lengths) / len(self._lengths)) if self._lengths else 0.0
        self._tf = [Counter(t) for t in self._tokens]
        self._idf = self._compute_idf()

    def _compute_idf(self) -> dict[str, float]:
        n = len(self.passages)
        df: Counter[str] = Counter()
        for tokens in self._tokens:
            df.update(set(tokens))
        # Standard BM25 idf with the +0.5 smoothing; floored at a small positive so
        # a term present in every passage still contributes a little.
        return {
            term: max(1e-6, math.log(1 + (n - freq + 0.5) / (freq + 0.5)))
            for term, freq in df.items()
        }

    def search(self, query: str, top_k: int = 5) -> list[ScoredPassage]:
        terms = tokenize(query)
        if not terms or not self.passages:
            return []

        scored: list[ScoredPassage] = []
        for index, passage in enumerate(self.passages):
            score = self._score(terms, index)
            if score > 0:
                scored.append(ScoredPassage(passage=passage, score=round(score, 4)))
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:top_k]

    def _score(self, terms: list[str], index: int) -> float:
        tf = self._tf[index]
        dl = self._lengths[index]
        denom_norm = K1 * (1 - B + B * (dl / self._avgdl if self._avgdl else 1.0))
        total = 0.0
        for term in set(terms):
            freq = tf.get(term, 0)
            if not freq:
                continue
            idf = self._idf.get(term, 0.0)
            total += idf * (freq * (K1 + 1)) / (freq + denom_norm)
        return total

    def __len__(self) -> int:
        return len(self.passages)
