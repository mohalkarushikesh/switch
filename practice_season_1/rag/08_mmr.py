"""
08_mmr.py -- Maximal Marginal Relevance (MMR): diverse retrieval.

THE PROBLEM. Plain "top-k by similarity" ranks every document purely by how
close it is to the query, then keeps the k closest. But the k closest are often
near-DUPLICATES of each other: if two docs say the same thing in different words,
both score high, and top-k happily returns BOTH. The context window then wastes
slots on redundant text and under-covers the rest of the query. For a broad
question ("how do I speed up my web app?") you would rather see one doc about
database indexing PLUS one about caching than two docs about indexing.

THE FIX (MMR, Carbonell & Goldstein, 1998). Build the result set greedily. At
each step pick the still-unselected doc that maximizes a blend of two things:
    - RELEVANCE to the query, and
    - NOVELTY: how UNLIKE the docs we have ALREADY selected it is.
Formally, the next pick is:

    next = argmax over remaining of
               lambda * sim(doc, query)
             - (1 - lambda) * max sim(doc, already_selected)

lambda in [0, 1] is the knob:
    lambda = 1.0 -> pure relevance == plain top-k (redundancy allowed).
    lambda = 0.5 -> balance relevance against novelty (diversity kicks in).
    lambda = 0.0 -> pure novelty (ignores the query -- rarely what you want).

The embedder / cosine here are the toy stand-ins from common.py; a real system
would embed with a sentence-transformer and store vectors in a vector DB. The
retrieval + MMR logic layered on top is the actual lesson.

Run:  python 08_mmr.py
"""

from common import CORPUS, embed, cosine


# --- A corpus with DELIBERATE redundancy ------------------------------------
# The shared CORPUS already has two near-identical database-performance docs
# (index 2 and 3) and one relevant-but-DISTINCT caching doc (index 4). To make
# the redundancy stark -- so plain top-k fills up entirely with database docs and
# pushes the caching doc off the list -- we append two more database paraphrases.
# All four database docs embed almost identically under the toy embedder (they
# share the slowness/speed/database meaning groups), which is exactly the
# real-world failure MMR is meant to counter.
EXTRA_DOCS = [
    # 10: another way to say "add an index to speed up a slow query" (~ doc 2/3)
    "Slow SQL queries run faster after you add an index to the table.",
    # 11: yet another database-tuning paraphrase (~ doc 2/3/10)
    "Optimize a sluggish database query by adding an index and avoiding table scans.",
]

DOCS = list(CORPUS) + EXTRA_DOCS         # indices 0..9 from CORPUS, 10..11 local


# --- Baseline retriever: plain top-k by cosine similarity -------------------
def similarity_scores(query_vec, doc_vecs):
    """Cosine of the query against every doc. This is what plain top-k ranks on."""
    return [cosine(query_vec, dv) for dv in doc_vecs]


def top_k(scores, k):
    """Return the k doc ids with the highest similarity (best-first)."""
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return order[:k]


# --- MMR re-ranker ----------------------------------------------------------
def mmr(query_vec, doc_vecs, candidates, k, lam):
    """
    Greedily select k doc ids from `candidates` using Maximal Marginal Relevance.

    In practice you do NOT run MMR over the whole corpus: you first retrieve a
    broad candidate pool by plain similarity, then MMR-rerank *within* that pool.
    `candidates` is that pool (a list of doc ids).

    At each step we score every not-yet-selected candidate by
        lam * sim(doc, query)  -  (1 - lam) * (max sim to anything already chosen)
    and take the argmax. The second term is the novelty penalty: it grows as a
    candidate looks more like something we have already picked, so duplicates get
    suppressed once their twin is in the set.
    """
    # Relevance-to-query is fixed for the whole run; compute it once.
    rel = {i: cosine(query_vec, doc_vecs[i]) for i in candidates}

    selected = []
    remaining = list(candidates)
    while remaining and len(selected) < k:
        best_id, best_score = None, None
        for i in remaining:
            if selected:
                # Redundancy = closeness to the MOST similar already-selected doc.
                redundancy = max(cosine(doc_vecs[i], doc_vecs[j]) for j in selected)
            else:
                redundancy = 0.0                      # first pick: nothing to be redundant with
            score = lam * rel[i] - (1.0 - lam) * redundancy
            # Strict '>' means ties break toward the lowest index (stable, predictable).
            if best_score is None or score > best_score:
                best_score, best_id = score, i
        selected.append(best_id)
        remaining.remove(best_id)
    return selected


# --- Pretty-printing helpers ------------------------------------------------
def show_selection(title, ids, scores):
    print("\n" + title)
    for rank, doc_id in enumerate(ids, start=1):
        print(f"  {rank}. [doc {doc_id:>2}] sim={scores[doc_id]:.3f}  {DOCS[doc_id]}")


if __name__ == "__main__":
    # A broad "speed up my web app" question. It leans on the database meaning
    # group (database/queries/tables) but also mentions web/app, so the caching
    # doc is genuinely relevant -- just less than the database docs.
    query = "how to speed up slow database queries and tables in my web app"
    print(f"Query: {query!r}")

    doc_vecs = [embed(d) for d in DOCS]              # real: vector_db.upsert(embeddings)
    q_vec = embed(query)
    scores = similarity_scores(q_vec, doc_vecs)

    # The candidate pool MMR chooses from: every doc with any relevance signal,
    # best-first. Zero-similarity docs (cats, space, health) never enter the pool.
    pool = [i for i in top_k(scores, len(DOCS)) if scores[i] > 0]
    print("\nCandidate pool (all docs with nonzero similarity), best-first:")
    for doc_id in pool:
        print(f"  [doc {doc_id:>2}] sim={scores[doc_id]:.3f}  {DOCS[doc_id]}")

    # --- (a) Plain top-k: watch it fill up with near-duplicates -------------
    # The four database docs (2, 3, 10, 11) all score ~0.85 and crowd out the
    # distinct caching doc (4, ~0.56), which lands just off the list. A reader
    # asking a broad question gets three ways to say "add an index" and nothing
    # about caching.
    plain = top_k(scores, 3)
    show_selection("(a) PLAIN TOP-3 (relevance only) -- redundant, all 'add an index':",
                   plain, scores)

    # --- (b) MMR at two lambda values ---------------------------------------
    # lambda = 0.9 : novelty penalty is tiny, so MMR behaves almost like top-k
    #                and still stacks up the database duplicates.
    mmr_hi = mmr(q_vec, doc_vecs, pool, k=3, lam=0.9)
    show_selection("(b) MMR, lambda=0.9 (mostly relevance) -- still redundant:",
                   mmr_hi, scores)

    # lambda = 0.5 : relevance and novelty carry equal weight. Once one database
    #                doc is chosen, its near-twins get heavily penalized, so the
    #                DISTINCT caching doc (4) wins the second slot. Same top
    #                relevance, far better COVERAGE of the question.
    mmr_bal = mmr(q_vec, doc_vecs, pool, k=3, lam=0.5)
    show_selection("(b) MMR, lambda=0.5 (balanced) -- diverse: keeps a DB doc + caching:",
                   mmr_bal, scores)

    # --- Takeaway -----------------------------------------------------------
    print("\n--- Takeaway ---------------------------------------------------")
    print("Plain top-k and MMR@0.9 return three interchangeable database docs.")
    print("MMR@0.5 swaps a duplicate for the distinct caching doc (doc 4),")
    print("covering BOTH sub-topics of a broad 'speed up my web app' question.")
    print("Use diversity (lower lambda) for broad/exploratory queries and when")
    print("filling a summarization context; keep lambda high when the user wants")
    print("the single most on-point passage and redundancy is not a concern.")
