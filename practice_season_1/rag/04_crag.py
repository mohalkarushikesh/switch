"""
04_crag.py -- CRAG: Corrective Retrieval-Augmented Generation.

Plain RAG blindly trusts whatever the retriever returns and stuffs it into the
prompt. If retrieval is off-topic, the model happily hallucinates on top of junk.

CRAG (Yan et al., 2024) adds a lightweight RETRIEVAL EVALUATOR that grades the
retrieved docs *before* generation, then takes a corrective action:

    CORRECT   (something clearly relevant) -> keep it, but REFINE: chop each doc
              into small "knowledge strips", drop the irrelevant strips, keep
              only the useful bits.
    INCORRECT (nothing relevant)           -> discard it and fall back to an
              external source (e.g. a web search).
    AMBIGUOUS (unsure)                     -> do BOTH: refine what we have AND
              pull in external knowledge, then combine.

Only then do we generate. The evaluator and web search are toy stand-ins; a real
system uses a small grader model and an actual search API.

Run:  python 04_crag.py
"""

from common import (CORPUS, embed, embed_corpus, cosine, tokenize,
                    content_tokens, lexical_coverage)

UPPER, LOWER = 0.50, 0.20        # relevance thresholds for the three-way decision


# --- Retrieval evaluator: how relevant is each doc to the query? ------------
def relevance(query, doc):
    # Blend semantic similarity with exact-term coverage; take the stronger cue.
    # A real CRAG uses a fine-tuned grader (e.g. a T5) that outputs this score.
    return max(cosine(embed(query), embed(doc)), lexical_coverage(query, doc))


def grade(best_score):
    if best_score >= UPPER:
        return "CORRECT"
    if best_score <= LOWER:
        return "INCORRECT"
    return "AMBIGUOUS"


# --- Corrective action: knowledge refinement (decompose -> filter -> recompose)
def refine(query, doc):
    """
    Split a doc into small strips (here: clauses split on commas) and keep only
    the strips that are themselves relevant to the query. This throws away the
    noise that rode along inside an otherwise-relevant document.
    """
    strips = [s.strip() for s in doc.replace(";", ",").split(",") if s.strip()]
    q = set(content_tokens(query))
    kept = [s for s in strips if q & set(tokenize(s))]     # strip shares a query word
    return " ".join(kept) if kept else doc                 # fall back to whole doc


# --- Corrective action: external fallback (simulated web search) ------------
def web_search(query):
    # Stand-in for a real search API call. A real CRAG issues the query to the
    # web and returns the top snippet.
    return f"[web] External result for {query!r}: (fetched from an outside source)"


def retrieve(query, doc_vecs, k=3):
    q = embed(query)
    scored = sorted(((i, cosine(q, dv)) for i, dv in enumerate(doc_vecs)),
                    key=lambda x: x[1], reverse=True)
    return [doc_id for doc_id, _ in scored[:k]]


def crag(query, doc_vecs):
    print(f"\n=== Query: {query!r} ===")
    retrieved = retrieve(query, doc_vecs)

    graded = [(doc_id, relevance(query, CORPUS[doc_id])) for doc_id in retrieved]
    for doc_id, score in graded:
        print(f"  eval: relevance={score:.2f}  {CORPUS[doc_id]}")

    best = max(score for _, score in graded)
    decision = grade(best)
    print(f"  -> decision: {decision} (best relevance = {best:.2f})")

    knowledge = []
    if decision in ("CORRECT", "AMBIGUOUS"):
        # Keep + refine the docs the evaluator liked.
        for doc_id, score in graded:
            if score >= UPPER:
                knowledge.append("internal: " + refine(query, CORPUS[doc_id]))
    if decision in ("INCORRECT", "AMBIGUOUS"):
        # Internal knowledge is untrustworthy -> reach outside.
        knowledge.append(web_search(query))

    print("  knowledge passed to the generator:")
    for k in knowledge:
        print(f"    - {k}")
    return knowledge


if __name__ == "__main__":
    doc_vecs = embed_corpus()

    # Good retrieval -> CORRECT -> refine and use the internal docs.
    crag("how do I make my database faster?", doc_vecs)

    # No relevant doc exists -> INCORRECT -> fall back to a web search.
    crag("what is a good recipe for pizza?", doc_vecs)
