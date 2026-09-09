"""
05_self_rag.py -- Self-RAG: retrieve on demand, then self-critique.

Plain RAG always retrieves and always trusts what it got. Self-RAG (Asai et al.,
2023) teaches the model to emit special "reflection tokens" that let it decide
and grade its own retrieval:

    Retrieve?  -> should I even look something up for this query, or just answer?
    ISREL      -> is this retrieved doc RELEVANT to the query?
    ISSUP      -> is my drafted answer actually SUPPORTED by (grounded in) the doc,
                  or am I making it up?   (fully / partial / no)
    ISUSE      -> how USEFUL is the final answer overall?   (1-5)

The model then keeps the candidate that scores best across these reflections.
The nice property: a doc can be on-topic (ISREL=relevant) yet NOT actually
support a concrete answer (ISSUP=no) -- Self-RAG catches that and prefers the
grounded candidate.

Here the reflections are computed with simple heuristics; a REAL Self-RAG model
generates these tokens itself, inline with the answer.

Run:  python 05_self_rag.py
"""

from common import (CORPUS, embed, embed_corpus, cosine, tokenize,
                    content_tokens, lexical_coverage)

GREETINGS = {"hello", "hi", "hey", "thanks", "thank", "bye", "goodbye"}


# --- Reflection: Retrieve? --------------------------------------------------
def need_retrieval(query):
    """Chit-chat / greetings need no documents; informational queries do."""
    toks = content_tokens(query)
    if not toks or set(tokenize(query)) & GREETINGS:   # tokenize drops the comma in "hello,"
        return False
    return True


# --- Reflection: ISREL / ISSUP / ISUSE for one candidate --------------------
def reflect(query, doc):
    relevance = cosine(embed(query), embed(doc))       # topical match
    grounding = lexical_coverage(query, doc)           # are the query's terms actually here?

    isrel = "relevant" if relevance >= 0.40 else "irrelevant"
    if grounding >= 0.50:
        issup = "fully"
    elif grounding > 0:
        issup = "partial"
    else:
        issup = "no"
    isuse = max(1, min(5, round(1 + 4 * relevance)))   # 1..5 usefulness
    return {"relevance": relevance, "grounding": grounding,
            "ISREL": isrel, "ISSUP": issup, "ISUSE": isuse}


def candidate_key(cand):
    """Rank candidates: relevant first, then well-supported, then useful."""
    support_rank = {"fully": 2, "partial": 1, "no": 0}
    return (cand["ISREL"] == "relevant",
            support_rank[cand["ISSUP"]],
            cand["ISUSE"])


def retrieve(query, doc_vecs, k=3):
    q = embed(query)
    scored = sorted(((i, cosine(q, dv)) for i, dv in enumerate(doc_vecs)),
                    key=lambda x: x[1], reverse=True)
    return [doc_id for doc_id, _ in scored[:k]]


def self_rag(query, doc_vecs):
    print(f"\n=== Query: {query!r} ===")

    # Reflection token #1: do we retrieve at all?
    if not need_retrieval(query):
        print("  Retrieve? = No  -> answering directly, no documents needed.")
        print("  Answer: (generated from the model's own knowledge)")
        return

    print("  Retrieve? = Yes  -> looking up documents and critiquing each.")
    candidates = []
    for doc_id in retrieve(query, doc_vecs):
        r = reflect(query, CORPUS[doc_id])
        r["doc_id"] = doc_id
        candidates.append(r)
        print(f"    ISREL={r['ISREL']:<10} ISSUP={r['ISSUP']:<7} "
              f"ISUSE={r['ISUSE']}  | {CORPUS[doc_id]}")

    best = max(candidates, key=candidate_key)
    if best["ISREL"] != "relevant":
        print("  All candidates judged irrelevant -> answer withheld / fall back.")
        return

    print(f"  -> chosen (relevant + best supported): {CORPUS[best['doc_id']]}")
    print(f"  Answer (grounded in that doc): {CORPUS[best['doc_id']]}")


if __name__ == "__main__":
    doc_vecs = embed_corpus()

    # Informational query: retrieve, then note that BOTH db docs are relevant but
    # only one is lexically SUPPORTED (contains "speed/slow/database") -> that one wins.
    self_rag("how do I speed up a slow database?", doc_vecs)

    # Social query: no retrieval needed at all.
    self_rag("hello, how are you today?", doc_vecs)
