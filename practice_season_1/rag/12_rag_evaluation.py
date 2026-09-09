"""
12_rag_evaluation.py -- Evaluating a RAG system with offline heuristic metrics.

Once you have a RAG pipeline, the hard question is: "is it any GOOD?" You cannot
improve what you cannot measure, so you need numbers for the two halves of the
system separately:

    RETRIEVAL quality  -- did we fetch the right documents?
    GENERATION quality -- given what we fetched, is the answer well-grounded and
                          on-topic?

This file implements simplified, deterministic stand-ins for the popular
RAGAS-style metrics so you can see WHAT each one measures and WHY it matters:

    1. CONTEXT PRECISION@k / CONTEXT RECALL@k  (retrieval)
         Precision@k : of the k docs we retrieved, what fraction were relevant?
                       (are we wasting context-window budget on junk?)
         Recall@k    : of all the relevant docs that exist, what fraction did we
                       actually retrieve? (did we miss evidence the answer needs?)

    2. FAITHFULNESS / GROUNDEDNESS  (generation)
         Of the claims the answer makes, what fraction are actually supported by
         the retrieved context? A low score means the model is HALLUCINATING --
         asserting things the evidence never said. We contrast a grounded answer
         (high) against a hallucinated one (low) so the point is visible.

    3. ANSWER RELEVANCE  (generation)
         Does the answer actually address the QUESTION, or does it wander /
         hedge? Measured as similarity between the answer and the query.

BIG CAVEAT: these are TOY, heuristic implementations. Real RAGAS-style metrics
usually use an LLM as a JUDGE -- e.g. faithfulness asks an LLM "is this claim
entailed by this context? yes/no", and answer-relevance asks an LLM to generate
questions the answer would answer, then compares them to the real query. Here we
substitute cheap lexical/embedding heuristics for that judge so everything runs
offline with just numpy. Where an LLM judge would go, a comment says so.

Run:  python 12_rag_evaluation.py
"""

from common import (CORPUS, embed, embed_corpus, cosine,
                    tokenize, content_tokens, lexical_coverage)


# --- The evaluation set (the "gold" labels) ---------------------------------
# A tiny labelled benchmark: each entry is a query plus the SET of doc ids a
# human annotator judged truly relevant. Building this by hand is the unglamorous
# but essential part of evaluation -- the metrics below are only as trustworthy
# as these labels. We keep the wording inside the toy embedder's known
# vocabulary (slow, database, query, index, caching, latency, machine learning,
# ...) so dense retrieval produces real signal.
EVAL_SET = [
    {
        "query": "how do I speed up a slow database query?",
        "relevant": {2, 3},   # both db-performance docs are on-topic
    },
    {
        "query": "how to cut response latency in web apps with caching?",
        "relevant": {4},      # only the caching doc
    },
    {
        "query": "what do machine learning models learn from training data?",
        "relevant": {5, 6},   # the programming/ML and the ML docs
    },
]


# --- Retrieval under test ----------------------------------------------------
# The thing we are grading. Here it is a plain dense retriever; in practice this
# would be whatever pipeline you want to score (hybrid, reranked, CRAG, ...).
def retrieve(query, doc_vecs, k):
    q = embed(query)
    scored = sorted(((i, cosine(q, dv)) for i, dv in enumerate(doc_vecs)),
                    key=lambda x: x[1], reverse=True)
    return [doc_id for doc_id, _ in scored[:k]]


# --- Metric 1a: Context Precision@k -----------------------------------------
def context_precision_at_k(retrieved, relevant):
    """
    Fraction of the RETRIEVED docs that are actually relevant.
    High precision = we did not pad the context with off-topic noise.
    """
    if not retrieved:
        return 0.0
    hits = sum(1 for doc_id in retrieved if doc_id in relevant)
    return hits / len(retrieved)


# --- Metric 1b: Context Recall@k --------------------------------------------
def context_recall_at_k(retrieved, relevant):
    """
    Fraction of the RELEVANT docs that we managed to retrieve.
    High recall = we did not leave necessary evidence behind. (An answer can only
    be grounded in evidence that made it into the context in the first place.)
    """
    if not relevant:
        return 1.0                      # nothing to find -> trivially complete
    found = sum(1 for doc_id in relevant if doc_id in set(retrieved))
    return found / len(relevant)


# --- Metric 2: Faithfulness / Groundedness ----------------------------------
def split_claims(answer):
    """
    Break an answer into individual "claims". A real system asks an LLM to
    enumerate the atomic factual claims; we cheaply approximate a claim with a
    sentence (split on '.'). Each sentence is then checked independently.
    """
    return [s.strip() for s in answer.split(".") if s.strip()]


def claim_supported(claim, context_docs):
    """
    Is a single claim backed by the retrieved context?

    Heuristic: the claim is "supported" if some context doc both shares enough of
    the claim's content words AND is semantically close to it. Requiring BOTH cues
    stops a claim from passing on one stray shared word alone. A REAL metric would
    ask an LLM judge:  # real: llm(f"Does CONTEXT entail CLAIM? yes/no")
    """
    for doc in context_docs:
        lexical = lexical_coverage(claim, doc)          # shared content words
        semantic = cosine(embed(claim), embed(doc))     # shared meaning
        if lexical >= 0.5 and semantic >= 0.5:
            return True
    return False


def faithfulness(answer, context_docs):
    """
    Fraction of the answer's claims that are grounded in the context.
    1.0 = every claim traceable to the evidence; low = the model invented things.
    """
    claims = split_claims(answer)
    if not claims:
        return 0.0
    supported = sum(1 for c in claims if claim_supported(c, context_docs))
    return supported / len(claims), claims   # also return claims for the report


# --- Metric 3: Answer Relevance ---------------------------------------------
def answer_relevance(answer, query):
    """
    How well the answer addresses the question. We use cosine similarity between
    the answer's and the query's embeddings: an on-topic answer lives near the
    query in semantic space; a rambling or evasive one drifts away.

    A REAL metric would ask an LLM to reverse-engineer the questions the answer
    seems to respond to, then compare those to the real query:
        # real: gen_qs = llm(f"What questions does this answer address? {answer}")
    """
    return cosine(embed(answer), embed(query))


# --- Reporting helpers -------------------------------------------------------
def banner(title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


if __name__ == "__main__":
    doc_vecs = embed_corpus()
    K = 3   # retrieve top-3; we grade precision/recall at this cutoff

    # ------------------------------------------------------------------
    # PART A -- RETRIEVAL METRICS across the whole evaluation set.
    # ------------------------------------------------------------------
    banner(f"PART A: RETRIEVAL QUALITY  (context precision & recall @ k={K})")
    p_sum = r_sum = 0.0
    for case in EVAL_SET:
        query, relevant = case["query"], case["relevant"]
        retrieved = retrieve(query, doc_vecs, K)
        prec = context_precision_at_k(retrieved, relevant)
        rec = context_recall_at_k(retrieved, relevant)
        p_sum += prec
        r_sum += rec
        print(f"\nQuery      : {query!r}")
        print(f"  retrieved ids : {retrieved}")
        print(f"  relevant ids  : {sorted(relevant)}  (the gold labels)")
        print(f"  precision@{K}  : {prec:.2f}   (relevant among retrieved)")
        print(f"  recall@{K}     : {rec:.2f}   (retrieved among relevant)")
    n = len(EVAL_SET)
    print(f"\n  MEAN precision@{K} = {p_sum / n:.2f}   MEAN recall@{K} = {r_sum / n:.2f}")
    print("  (aggregate scores like these are what you track as you tune the pipeline)")

    # ------------------------------------------------------------------
    # PART B -- GENERATION METRICS: grounded vs hallucinated, side by side.
    # We freeze ONE query and its retrieved context, then score two candidate
    # answers so the contrast is apples-to-apples.
    # ------------------------------------------------------------------
    banner("PART B: GENERATION QUALITY  (faithfulness + answer relevance)")

    query = "how do I speed up a slow database query?"
    retrieved = retrieve(query, doc_vecs, K)
    context_docs = [CORPUS[i] for i in retrieved]

    print(f"\nQuery   : {query!r}")
    print("Context passed to the generator (the retrieved docs):")
    for i in retrieved:
        print(f"   [{i}] {CORPUS[i]}")

    # A GROUNDED answer: every sentence is traceable to the db-performance docs.
    grounded = ("To speed up a slow database query, add an index on the filtered "
                "column. Optimizing sluggish SQL also means avoiding full table scans.")

    # A HALLUCINATED answer: it opens with a real, grounded claim, then invents
    # two sentences about space and health that the context NEVER mentions.
    hallucinated = ("To speed up a slow database query, add an index. "
                    "The space telescope also captured images of distant galaxies. "
                    "Regular exercise improves cardiovascular fitness too.")

    for label, ans in [("GROUNDED answer", grounded),
                       ("HALLUCINATED answer", hallucinated)]:
        faith, claims = faithfulness(ans, context_docs)
        relev = answer_relevance(ans, query)
        print(f"\n--- {label} ---")
        print(f'  "{ans}"')
        print("  per-claim grounding check (real systems use an LLM judge):")
        for c in claims:
            ok = claim_supported(c, context_docs)
            print(f"     [{'supported' if ok else 'UNSUPPORTED'}]  {c}")
        print(f"  FAITHFULNESS    = {faith:.2f}   (fraction of claims backed by context)")
        print(f"  ANSWER RELEVANCE= {relev:.2f}   (answer-vs-query similarity)")

    print("\nTakeaway: both answers look fluent, but faithfulness exposes the")
    print("hallucinated one -- its space/health claims have no support in the")
    print("retrieved context, so a chunk of its claims score UNSUPPORTED.")
