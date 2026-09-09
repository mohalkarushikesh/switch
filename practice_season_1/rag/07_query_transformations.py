"""
07_query_transformations.py -- Transforming the QUERY before retrieval.

Retrieval quality is capped by how the user phrased the question. A vague or
narrow phrasing ("make my app quicker") embeds into a thin, lop-sided vector and
only pulls back whatever happens to match those exact words -- so genuinely
relevant docs get missed (a RECALL problem). Instead of touching the index, we
rewrite the QUERY first. Three classic transforms:

    1. MULTI-QUERY / RAG-FUSION : ask an LLM for several paraphrases/expansions
       of the one query, retrieve for EACH, then fuse the ranked lists with
       Reciprocal Rank Fusion (RRF). Different phrasings hit different docs; RRF
       rewards docs that several variants agree on, so a doc the original
       phrasing missed can still surface.

    2. QUERY DECOMPOSITION       : split a compound question ("do A AND B?") into
       focused sub-questions and retrieve for each. One combined embedding is a
       muddy average of two topics; two clean sub-queries each retrieve sharply.

    3. STEP-BACK                 : generate a BROADER, more general question to
       fetch background context that a hyper-specific query would skip over.
       Used alongside the specific query, not instead of it.

(HyDE -- see 03 -- is ALSO a query transform: it rewrites the query into a
hypothetical ANSWER before embedding. Same family, different trick.)

All the "LLM rewrites" here are rule-based TOY STUBS -- each shows the real
llm() call it stands in for. Retrieval is the offline toy embedder from common.

Run:  python 07_query_transformations.py
"""

from common import CORPUS, embed, embed_corpus, cosine


# --- Toy retriever ----------------------------------------------------------
# Dense (semantic) search over the shared corpus. A real system queries a vector
# DB; here we just cosine the query vector against every pre-embedded doc.
def dense_search(query, doc_vecs):
    q = embed(query)
    scored = [(i, cosine(q, dv)) for i, dv in enumerate(doc_vecs)]
    return sorted(scored, key=lambda x: x[1], reverse=True)


def hits(ranking, k=5):
    """
    Keep only a retriever's ACTUAL hits (positive score), capped at k. The toy
    embedder scores every unrelated doc 0.0; their order is arbitrary, so feeding
    those zero-score ties into fusion would let irrelevant docs drift upward.
    """
    return [(doc_id, s) for doc_id, s in ranking if s > 0][:k]


# --- Reciprocal Rank Fusion (reimplemented locally) -------------------------
# NOTE: 01_hybrid_retrieval.py also has an RRF, but modules whose names start
# with a digit are not importable, so we reimplement it here (that is expected).
def rrf(rankings, k=60):
    """
    rankings : list of ranked lists, each [(doc_id, score), ...] best-first.
    Each list adds 1 / (k + rank) to a doc's fused score (rank starts at 1). A
    doc ranked highly by MANY variants accumulates the most; k=60 damps the pull
    of any single list's top spot so no one phrasing dominates the fusion.
    """
    fused = {}
    for ranking in rankings:
        for rank, (doc_id, _score) in enumerate(ranking, start=1):
            fused[doc_id] = fused.get(doc_id, 0.0) + 1.0 / (k + rank)
    return sorted(fused.items(), key=lambda x: x[1], reverse=True)


def show(title, ranking, topn=4):
    print("\n" + title)
    if not ranking:
        print("    (no hits)")
        return
    for rank, (doc_id, score) in enumerate(ranking[:topn], start=1):
        print(f"  {rank}. (score={score:.4f})  {CORPUS[doc_id]}")


# --- TOY LLM query-transform stubs ------------------------------------------
# Each function fakes an LLM rewrite with a hand-written rule. In production the
# body would be a single llm(prompt) call whose prompt is shown in the comment.

def llm_multi_query(query):
    """
    MULTI-QUERY expansion. Real call:
        # variants = llm(f"Rewrite this search query 4 different ways, varying "
        #                 f"wording and angle, one per line:\\n{query}")
    We hard-code plausible rewrites of "make my app quicker". Crucially the
    original is vague (only "app" is a known topic word), so its variants pull in
    DIFFERENT, more specific vocabulary -- web latency, caching, AND databases.
    """
    return [
        "speed up a slow web app",        # slowness + speed + web/cache dims
        "reduce response latency",        # web/cache + slowness dims
        "caching frequent results",       # web/cache dim
        "optimize a slow database query", # speed + databases dims  <- new topic!
    ]


def llm_decompose(query):
    """
    QUERY DECOMPOSITION. Real call:
        # subs = llm(f"Break this into independent sub-questions, one per line:\\n{query}")
    Split the compound question on its 'and' into two single-topic sub-queries.
    """
    return [
        "speed up a slow database query",   # database-performance half
        "cut web app response latency",     # web/caching half
    ]


def llm_step_back(query):
    """
    STEP-BACK prompting. Real call:
        # general = llm(f"What broader, more general question should I answer "
        #               f"first to give background for: {query}")
    Map a hyper-specific question ("why this one SQL symptom?") up to the general
    principle behind it ("why is my whole app slow / how do I make it faster?").
    Deliberately broad wording so it reaches beyond the narrow SQL doc.
    """
    return "how do I make a slow app run faster overall?"


# --- 1. MULTI-QUERY / RAG-FUSION --------------------------------------------
def demo_multi_query(doc_vecs):
    print("\n" + "=" * 70)
    print("1. MULTI-QUERY / RAG-FUSION")
    print("=" * 70)

    original = "make my app quicker"
    print(f"Original query: {original!r}")

    # Baseline: retrieve with the single original phrasing.
    base = hits(dense_search(original, doc_vecs))
    show("Baseline -- single phrasing (misses the DATABASE fix entirely):", base)

    # Expand into variants and retrieve for each.
    variants = llm_multi_query(original)
    print("\nLLM-generated variants + their individual retrieval:")
    per_variant = []
    for v in variants:
        ranking = hits(dense_search(v, doc_vecs))
        per_variant.append(ranking)
        top = CORPUS[ranking[0][0]] if ranking else "(no hits)"
        print(f"  - {v!r}")
        print(f"      top hit -> {top}")

    # Fuse all variant rankings (RAG-fusion). We do NOT include the vague
    # original -- the whole point is to let the sharper variants vote.
    fused = rrf(per_variant)
    show("Fused via RRF -- surfaces the database doc the original MISSED:", fused)

    base_ids = {doc_id for doc_id, _ in base}
    fused_ids = {doc_id for doc_id, _ in fused}
    gained = fused_ids - base_ids
    print("\n  Docs recovered by fusion that the single query missed:")
    for doc_id in sorted(gained):
        print(f"    + [{doc_id}] {CORPUS[doc_id]}")


# --- 2. QUERY DECOMPOSITION -------------------------------------------------
def demo_decomposition(doc_vecs):
    print("\n" + "=" * 70)
    print("2. QUERY DECOMPOSITION")
    print("=" * 70)

    compound = "how do I speed up a slow database and cut web app latency?"
    print(f"Compound query: {compound!r}")

    # One embedding of the whole thing is a blurry average of two topics.
    blurry = hits(dense_search(compound, doc_vecs))
    show("Single combined query -- one topic tends to crowd out the other:", blurry)

    # Split, retrieve each half cleanly, and report both answer sets.
    subs = llm_decompose(compound)
    print("\nDecomposed sub-questions + their retrieval:")
    answers = {}
    for s in subs:
        ranking = hits(dense_search(s, doc_vecs))
        answers[s] = ranking
        show(f"  sub-question {s!r}:", ranking, topn=2)

    print("\n  Each sub-question is answered by its OWN best doc:")
    for s, ranking in answers.items():
        if ranking:
            print(f"    {s!r} -> [{ranking[0][0]}] {CORPUS[ranking[0][0]]}")


# --- 3. STEP-BACK -----------------------------------------------------------
def demo_step_back(doc_vecs):
    print("\n" + "=" * 70)
    print("3. STEP-BACK")
    print("=" * 70)

    specific = "why is my sql query doing a full table scan"
    print(f"Specific query: {specific!r}")
    specific_hits = hits(dense_search(specific, doc_vecs))
    show("Specific retrieval -- pinpoints the exact-symptom doc:", specific_hits)

    # Step back to the general principle to fetch background context.
    general = llm_step_back(specific)
    print(f"\nStep-back (broader) query: {general!r}")
    general_hits = hits(dense_search(general, doc_vecs))
    show("Step-back retrieval -- pulls in the general-principle doc(s):", general_hits)

    print("\n  How they COMPLEMENT each other (specific detail + broad background):")
    spec_ids = [doc_id for doc_id, _ in specific_hits]
    gen_ids = [doc_id for doc_id, _ in general_hits]
    context = list(dict.fromkeys(spec_ids + gen_ids))   # union, order-preserving
    for doc_id in context:
        origin = []
        if doc_id in spec_ids:
            origin.append("specific")
        if doc_id in gen_ids:
            origin.append("step-back")
        print(f"    [{doc_id}] ({'+'.join(origin)}) {CORPUS[doc_id]}")

    # The payoff: the broad query drags in background the narrow one skipped.
    background = [doc_id for doc_id in gen_ids if doc_id not in spec_ids]
    print("\n  Background context the specific query alone would have MISSED:")
    for doc_id in background:
        print(f"    + [{doc_id}] {CORPUS[doc_id]}")


if __name__ == "__main__":
    doc_vecs = embed_corpus()
    demo_multi_query(doc_vecs)
    demo_decomposition(doc_vecs)
    demo_step_back(doc_vecs)
