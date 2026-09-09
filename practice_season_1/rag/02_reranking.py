"""
02_reranking.py -- two-stage retrieval: fast retrieve, then precise rerank.

Retrieval is usually two stages:

    Stage 1  RETRIEVE (bi-encoder)   : embed the query and every document
             SEPARATELY, compare with cosine. Cheap and fast -- doc vectors are
             precomputed -- so it can scan millions of docs. But because query
             and doc never "meet", it can only judge coarse topical similarity.

    Stage 2  RERANK (cross-encoder)  : take the top-K candidates from stage 1 and
             score each (query, doc) PAIR jointly, reading them together. Much
             more accurate, but too expensive to run over the whole corpus --
             which is why we only rerank a shortlist.

Below, the bi-encoder can't tell two same-topic database docs apart (their
coarse vectors are identical), so it lists them tied. The cross-encoder reads
the query alongside each doc, notices which one literally contains "full table
scans", and lifts it to the top.

The toy cross-encoder here = 0.5*semantic + 0.5*exact-term-coverage. A REAL one
is a transformer (e.g. a BERT cross-encoder, or Cohere/Voyage rerank) fed the
concatenated query+doc.

Run:  python 02_reranking.py
"""

from common import CORPUS, embed, embed_corpus, cosine, lexical_coverage


# --- Stage 1: bi-encoder retrieval (fast, approximate) ----------------------
def retrieve(query, doc_vecs, k=4):
    q = embed(query)
    scored = [(i, cosine(q, dv)) for i, dv in enumerate(doc_vecs)]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]                                # shortlist of K candidates


# --- Stage 2: cross-encoder rerank (slow, precise) --------------------------
def cross_encoder_score(query, doc):
    """
    Stand-in for a real cross-encoder. A real model would jointly encode the
    query and doc; we approximate "reading them together" by blending semantic
    similarity with how many of the query's exact terms actually appear.
    """
    semantic = cosine(embed(query), embed(doc))      # topical match (like stage 1)
    lexical = lexical_coverage(query, doc)           # did the exact query words show up?
    return 0.5 * semantic + 0.5 * lexical


def rerank(query, candidates):
    rescored = [(doc_id, cross_encoder_score(query, CORPUS[doc_id]))
                for doc_id, _ in candidates]
    return sorted(rescored, key=lambda x: x[1], reverse=True)


def show(title, ranking):
    print("\n" + title)
    for rank, (doc_id, score) in enumerate(ranking, start=1):
        print(f"  {rank}. (score={score:.4f})  {CORPUS[doc_id]}")


if __name__ == "__main__":
    query = "how can I avoid full table scans?"
    print(f"Query: {query!r}")

    doc_vecs = embed_corpus()
    candidates = retrieve(query, doc_vecs, k=4)      # stage 1 shortlist
    reranked = rerank(query, candidates)             # stage 2 reorder

    # Note the tie at the top of stage 1: the bi-encoder sees the two database
    # docs as the same topic and can't separate them.
    show("Stage 1 -- bi-encoder retrieval (note the tied top scores):", candidates)
    # The cross-encoder spots the literal 'full table scans' and promotes it.
    show("Stage 2 -- cross-encoder rerank (the exact-match doc wins):", reranked)
