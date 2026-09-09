"""
01_hybrid_retrieval.py -- Dense + BM25 hybrid retrieval.

Two retrievers see the world differently:

    BM25 (lexical)   : rewards EXACT word overlap. Great for rare/precise terms
                       ("index", an error code, a product name) but blind to
                       synonyms -- "slow" and "sluggish" look unrelated to it.

    Dense (semantic) : rewards MEANING overlap via embeddings. Catches
                       paraphrases ("slow" ~ "sluggish") but can miss a precise
                       keyword that didn't move the embedding much.

Hybrid retrieval runs BOTH and fuses their rankings, keeping the strengths of
each. We fuse with Reciprocal Rank Fusion (RRF), which combines *ranks* (not raw
scores) -- so we avoid the headache of putting BM25 scores and cosine scores on
the same scale.

Run:  python 01_hybrid_retrieval.py
"""

import math
from common import CORPUS, tokenize, embed, embed_corpus, cosine


# --- BM25: the classic lexical retriever, implemented from scratch ----------
class BM25:
    def __init__(self, corpus, k1=1.5, b=0.75):
        self.k1, self.b = k1, b                                   # standard Okapi knobs
        self.docs = [tokenize(d) for d in corpus]                 # pre-tokenized docs
        self.N = len(self.docs)
        self.avgdl = sum(len(d) for d in self.docs) / self.N      # average document length
        # document frequency: in how many documents does each term appear at least once?
        self.df = {}
        for doc in self.docs:
            for term in set(doc):
                self.df[term] = self.df.get(term, 0) + 1

    def idf(self, term):
        # Inverse document frequency: rare terms carry more signal -> higher idf.
        n = self.df.get(term, 0)
        return math.log(1 + (self.N - n + 0.5) / (n + 0.5))

    def score(self, query, doc_tokens):
        score = 0.0
        dl = len(doc_tokens)
        for term in tokenize(query):
            tf = doc_tokens.count(term)                           # term frequency in this doc
            if tf == 0:
                continue
            # tf is saturated by k1 (repeating a word helps with diminishing
            # returns) and length-normalized by b (long docs don't win for free).
            num = tf * (self.k1 + 1)
            den = tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
            score += self.idf(term) * num / den
        return score

    def rank(self, query):
        scored = [(i, self.score(query, doc)) for i, doc in enumerate(self.docs)]
        return sorted(scored, key=lambda x: x[1], reverse=True)


# --- Dense: the semantic retriever ------------------------------------------
def dense_rank(query, doc_vecs):
    q = embed(query)
    scored = [(i, cosine(q, dv)) for i, dv in enumerate(doc_vecs)]
    return sorted(scored, key=lambda x: x[1], reverse=True)


# --- Fusion: Reciprocal Rank Fusion -----------------------------------------
def reciprocal_rank_fusion(rankings, k=60):
    """
    rankings : list of ranked lists, each [(doc_id, score), ...] best-first.
    Each list contributes 1 / (k + rank) to a doc's fused score (rank starts at 1).
    A doc ranked highly by BOTH systems accumulates the most. k dampens the pull
    of the very top ranks so no single list dominates. (k=60 is the common default.)
    """
    fused = {}
    for ranking in rankings:
        for rank, (doc_id, _score) in enumerate(ranking, start=1):
            fused[doc_id] = fused.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(fused.items(), key=lambda x: x[1], reverse=True)


def top_hits(ranking, k=5):
    """
    A retriever returns only its ACTUAL hits, not the whole corpus. This matters
    for fusion: BM25 scores every non-matching doc 0, and the order among those
    ties is arbitrary -- feeding them into RRF lets an irrelevant doc sneak up the
    fused list. So we fuse only positive-scoring hits, capped at k per retriever.
    """
    return [(doc_id, s) for doc_id, s in ranking if s > 0][:k]


def show(title, ranking, topn=4):
    print("\n" + title)
    for rank, (doc_id, score) in enumerate(ranking[:topn], start=1):
        print(f"  {rank}. (score={score:.4f})  {CORPUS[doc_id]}")


if __name__ == "__main__":
    query = "how do I make my database queries faster?"
    print(f"Query: {query!r}")

    bm25 = BM25(CORPUS)
    doc_vecs = embed_corpus()

    bm25_ranking = bm25.rank(query)
    dense_ranking = dense_rank(query, doc_vecs)
    # Fuse only each retriever's real hits (see top_hits for why).
    fused_ranking = reciprocal_rank_fusion([top_hits(bm25_ranking), top_hits(dense_ranking)])

    # BM25 latches onto the literal word "database" (the 'index' doc).
    show("BM25 (lexical) -- locks onto the exact keyword 'database':", bm25_ranking)
    # Dense also pulls in the 'sluggish SQL' doc, which shares almost no words.
    show("Dense (semantic) -- also surfaces the 'sluggish SQL' paraphrase:", dense_ranking)
    # RRF keeps the keyword hit AND the paraphrase near the top.
    show("Hybrid via RRF -- best of both, paraphrase + keyword together:", fused_ranking)
