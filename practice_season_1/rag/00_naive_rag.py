"""
00_naive_rag.py -- Naive end-to-end RAG baseline (the anchor example).

This is the SIMPLEST possible Retrieval-Augmented Generation pipeline -- the
plain baseline that every other file in this folder improves upon.

The problem RAG solves: a language model only knows what was baked into its
weights at training time. To answer questions about YOUR documents, you fetch
the relevant ones at query time and hand them to the model as context. The model
then answers *grounded in what you retrieved* instead of from memory alone.

How naive RAG works -- four explicit stages, all shown below:

    1. INDEX    : embed every document once, up front, into vectors you can
                  search. (Here docs are already sentence-sized, so one vector
                  per doc. A real system stores these in a vector database.)
    2. RETRIEVE : embed the user's query the same way and pull the top-k docs
                  by cosine similarity -- the ones whose meaning is closest.
    3. AUGMENT  : stitch the retrieved docs into a prompt string as "context",
                  then append the question. (We print the assembled prompt so
                  you can literally see what the model would receive.)
    4. GENERATE : feed that prompt to an LLM and return its answer.

The embedder and the "LLM" here are TOY STAND-INS so this runs fully offline
with just numpy -- no models to download, no API keys. Where a real model call
would go, a comment shows it (e.g. "# real: answer = llm(prompt)").

Run:  python 00_naive_rag.py
"""

from common import CORPUS, embed, embed_corpus, cosine


# --- Stage 2 helper: RETRIEVE -----------------------------------------------
def retrieve(query, doc_vecs, k=2):
    """
    Rank every document by cosine similarity to the query and return the top-k.

    This is the whole of "retrieval" in naive RAG: embed the query with the same
    embedder used at index time, compare against each stored doc vector, sort,
    take the best k. No reranking, no filtering, no thresholds -- it ALWAYS
    returns k docs, even if none are actually relevant (a key weakness; see below).

    Returns a list of (doc_id, score) best-first.
    """
    q = embed(query)                                          # same embedder as INDEX -- must match
    scored = [(i, cosine(q, dv)) for i, dv in enumerate(doc_vecs)]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]


# --- Stage 3 helper: AUGMENT ------------------------------------------------
def build_prompt(query, retrieved):
    """
    Assemble the prompt the model will see: the retrieved docs as numbered
    context, then an instruction, then the question. This "context stuffing" is
    the heart of RAG -- the retrieved text becomes part of the input, so the
    model can ground its answer in it instead of relying on parametric memory.
    """
    context = "\n".join(f"  [{n}] {CORPUS[doc_id]}"
                        for n, (doc_id, _score) in enumerate(retrieved, start=1))
    return (
        "Answer the question using ONLY the context below.\n"
        "Context:\n"
        f"{context}\n"
        f"Question: {query}\n"
        "Answer:"
    )


# --- Stage 4 helper: GENERATE (TOY STUB) ------------------------------------
def fake_llm(prompt, retrieved):
    """
    A clearly-labelled FAKE LLM. A real model would read `prompt` and compose a
    fluent answer:
        # real: answer = llm(prompt)
    To stay offline AND honest, this stub does not invent anything: it simply
    echoes back the single top-retrieved sentence as the grounded answer. That
    keeps the answer strictly traceable to retrieved context -- which is exactly
    what a well-behaved RAG answer should be.

    (`prompt` is accepted to mirror the real signature `llm(prompt)`, even though
    this stub reads its answer straight from the retrieved doc.)
    """
    if not retrieved:
        return "I don't have any context to answer that."
    top_doc_id = retrieved[0][0]
    return f"Based on the retrieved context: {CORPUS[top_doc_id]}"


# --- The full naive pipeline: INDEX -> RETRIEVE -> AUGMENT -> GENERATE -------
def naive_rag(query, doc_vecs):
    print(f"\n=== Query: {query!r} ===")

    # 2. RETRIEVE
    retrieved = retrieve(query, doc_vecs, k=2)
    print("\n[RETRIEVE] top-k docs by cosine similarity:")
    for rank, (doc_id, score) in enumerate(retrieved, start=1):
        print(f"  {rank}. (cos={score:.3f})  {CORPUS[doc_id]}")

    # 3. AUGMENT
    prompt = build_prompt(query, retrieved)
    print("\n[AUGMENT] assembled prompt handed to the model:")
    for line in prompt.splitlines():
        print(f"  | {line}")

    # 4. GENERATE
    answer = fake_llm(prompt, retrieved)      # real: answer = llm(prompt)
    print("\n[GENERATE] model answer (toy LLM, grounded in retrieval):")
    print(f"  {answer}")
    return answer


if __name__ == "__main__":
    # 1. INDEX -- embed the whole corpus once, up front. In a real system these
    # vectors live in a vector database and are computed only when docs change.
    doc_vecs = embed_corpus()
    print(f"[INDEX] embedded {len(doc_vecs)} documents "
          f"into {len(doc_vecs[0])}-dim vectors (done once, reused per query).")

    # An in-vocabulary query: every content word ("speed", "slow", "database")
    # lives in the toy embedder's semantic groups, so retrieval gets real signal.
    naive_rag("how do I speed up a slow database?", doc_vecs)

    # --- The point: where the baseline FAILS ---------------------------------
    # Naive RAG ALWAYS retrieves k docs and BLINDLY trusts them. Ask something
    # the corpus knows nothing about and it will still return its two "closest"
    # docs -- and the stub will confidently answer from that irrelevant context.
    naive_rag("what is a good recipe for pizza?", doc_vecs)

    # --- Baseline weaknesses, and where this folder fixes each ---------------
    print("\n" + "=" * 68)
    print("NAIVE RAG WEAKNESSES (watch the pizza query above -- cos ~ 0.0,")
    print("yet it still retrieved and answered from unrelated docs):")
    print("  - Single retriever only: lexical vs semantic blind spots")
    print("      -> fixed in 01_hybrid_retrieval.py (BM25 + dense, fused via RRF)")
    print("  - No reranking: top-k by raw similarity may mis-order results")
    print("      -> fixed in 02 (cross-encoder reranking)")
    print("  - Literal query: no rewriting/expansion of vague questions")
    print("      -> fixed in 03 (HyDE-style query transformation)")
    print("  - Blindly trusts retrieval: no relevance check before generating")
    print("      -> fixed in 04_crag.py (grade docs, correct or fall back)")
    print("  - No grounding check on the answer itself")
    print("      -> fixed in 05_self_rag.py (self-critique / reflection)")
