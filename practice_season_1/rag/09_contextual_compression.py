"""
09_contextual_compression.py -- Contextual compression / post-retrieval filtering.

THE PROBLEM
    Retrieval gives you whole documents, but only a few sentences inside them
    actually answer the query. Stuffing the full docs into the prompt wastes
    tokens (money + latency) and, worse, buries the useful lines in noise that
    can distract the generator. We want to shrink the context to just the parts
    that matter BEFORE we call the LLM.

HOW IT WORKS -- two layers, applied after retrieval and before generation:
    1. DOCUMENT FILTERING  ("LLMChainFilter"-style): score each RETRIEVED doc's
       relevance to the query and drop the ones below a threshold. A whole doc
       that only looked relevant (or was a weak hit) gets thrown out entirely.
    2. EXTRACTIVE COMPRESSION ("LLMChainExtractor"-style): within each doc that
       survived, split it into sentences and keep only the sentences that are
       themselves relevant to the query. This strips the "rode-along" noise
       inside an otherwise-useful document.

NOT THE SAME AS CRAG (see 04_crag.py):
    CRAG is about CORRECTNESS -- it grades retrieval and, if it's bad, CORRECTS
    it (refines strips OR falls back to web search) so the answer isn't built on
    junk. Contextual compression assumes retrieval is already good enough and is
    about EFFICIENCY -- cutting already-relevant results down to fewer tokens.
    (04 decides "should I even trust this?"; 09 decides "which words are worth
    paying for?")

The relevance scorer here is the toy embedder from common.py; both the doc
filter and the sentence extractor are stand-ins for real LLM calls -- the
comments show the llm() call each one replaces.

Run:  python 09_contextual_compression.py
"""

import re
from common import embed, cosine, content_tokens, tokenize


# --- Local multi-sentence corpus --------------------------------------------
# The shared CORPUS is one sentence per doc, so there would be nothing to
# compress WITHIN a doc. Compression only shows up when a single document mixes
# relevant lines with noise -- so we define our own multi-sentence docs here.
# Every sentence uses SEMANTIC_GROUPS vocabulary (slow/speed/database/query/
# index/cache/web/app plus animal/space/health "noise") so the toy embedder
# actually produces a relevance signal we can filter on.
DOCS = [
    # Doc 0: mostly on-topic (db speed) with two off-topic noise sentences.
    "To speed up a slow database query, add an index on the filtered column. "
    "Avoiding full table scans keeps SQL fast even as tables grow. "
    "The office cat napped on the warm windowsill all afternoon. "
    "Our team also loves playing fetch with dogs at the park after work.",

    # Doc 1: on-topic (web/caching speed) with two off-topic noise sentences.
    "Caching frequent results can cut response latency in web apps. "
    "A warm cache keeps the app fast under heavy load. "
    "The space telescope captured stunning images of distant galaxies. "
    "Regular exercise improves cardiovascular fitness and lowers stress.",

    # Doc 2: pure noise (animals + health). It is a weak retrieval hit and should
    # be DROPPED entirely by the document filter -- nothing here is worth keeping.
    "The cat napped while the dogs ran to fetch a ball at the park. "
    "A balanced diet of vegetables and fruits supports good health. "
    "Regular exercise improves fitness and lowers stress.",
]

# Thresholds. Tuned for the toy embedder so the demo visibly separates the
# relevant material from the noise. A real system exposes these as knobs too.
DOC_KEEP_THRESHOLD = 0.25    # min doc-level relevance to survive the filter
SENT_KEEP_THRESHOLD = 0.15   # min sentence-level relevance to be extracted


# --- Helpers ----------------------------------------------------------------
def split_sentences(doc):
    """Naive sentence splitter (good enough for the demo)."""
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", doc) if s.strip()]


def relevance(query, text):
    """
    How relevant is a piece of text to the query?

    Toy scorer: semantic cosine, backed up by exact content-word overlap so a
    short line with the right keyword isn't unfairly penalised by the embedder.

    A REAL contextual-compression pipeline asks an LLM to judge relevance, e.g.
        # real: llm(f"Is this text relevant to '{query}'? Score 0-1:\n{text}")
    """
    sem = cosine(embed(query), embed(text))
    q = content_tokens(query)
    overlap = 0.0
    if q:
        d = set(tokenize(text))
        overlap = sum(1 for t in q if t in d) / len(q)
    return max(sem, overlap)


def count(text):
    """Return (chars, words) so we can report the compression ratio."""
    return len(text), len(text.split())


# --- Layer 1: document filtering (LLMChainFilter-style) ---------------------
def filter_documents(query, docs):
    """
    Keep only whole docs whose relevance clears DOC_KEEP_THRESHOLD; drop the rest.

    Each keep/drop here stands in for a boolean LLM judgement:
        # real: llm(f"Does this document help answer '{query}'? yes/no\n{doc}")
    """
    kept, dropped = [], []
    for i, doc in enumerate(docs):
        score = relevance(query, doc)
        (kept if score >= DOC_KEEP_THRESHOLD else dropped).append((i, doc, score))
    return kept, dropped


# --- Layer 2: extractive compression (LLMChainExtractor-style) --------------
def compress_document(query, doc):
    """
    Keep only the sentences in `doc` that are relevant to the query; drop noise.

    Each sentence-level decision stands in for an extractive LLM call:
        # real: llm(f"Extract only the parts of this text relevant to "
        #            f"'{query}', or return nothing:\n{sentence}")
    """
    kept = []
    for sent in split_sentences(doc):
        if relevance(query, sent) >= SENT_KEEP_THRESHOLD:
            kept.append(sent)
    # If nothing clears the bar, fall back to the single best sentence so we
    # never hand the generator an empty doc.
    if not kept:
        sents = split_sentences(doc)
        kept = [max(sents, key=lambda s: relevance(query, s))] if sents else []
    return " ".join(kept)


# --- Orchestration: retrieve -> filter -> compress --------------------------
def contextual_compression(query, docs):
    print(f"\n=== Query: {query!r} ===")

    # (Retrieval is assumed already done: `docs` is what the retriever handed us.
    # Compression is a POST-retrieval step, so we start from the retrieved set.)
    original = "\n".join(docs)
    o_chars, o_words = count(original)
    print("\n[0] ORIGINAL retrieved context (what plain RAG would send):")
    for i, doc in enumerate(docs):
        print(f"    doc{i}: {doc}")
    print(f"    -> size: {o_chars} chars / {o_words} words")

    # Layer 1: drop whole docs that aren't relevant enough.
    kept, dropped = filter_documents(query, docs)
    print("\n[1] DOCUMENT FILTER (LLMChainFilter stub):")
    for i, _doc, score in kept:
        print(f"    KEEP doc{i}  (relevance={score:.2f})")
    for i, _doc, score in dropped:
        print(f"    DROP doc{i}  (relevance={score:.2f})  <- below {DOC_KEEP_THRESHOLD}")

    # Layer 2: within each surviving doc, keep only the relevant sentences.
    print("\n[2] EXTRACTIVE COMPRESSION (LLMChainExtractor stub):")
    compressed_docs = []
    for i, doc, _score in kept:
        before = split_sentences(doc)
        comp = compress_document(query, doc)
        after = split_sentences(comp)
        compressed_docs.append(comp)
        print(f"    doc{i}: kept {len(after)}/{len(before)} sentences")
        for sent in before:
            mark = "keep" if sent in after else "drop"
            print(f"        [{mark}] ({relevance(query, sent):.2f}) {sent}")

    compressed = "\n".join(compressed_docs)
    c_chars, c_words = count(compressed)
    print("\n[3] COMPRESSED context (what we actually send to the generator):")
    for i, comp in zip([k[0] for k in kept], compressed_docs):
        print(f"    doc{i}: {comp}")

    # Report the payoff: fewer chars/words -> fewer tokens -> cheaper, sharper.
    pct = (1 - c_chars / o_chars) * 100 if o_chars else 0.0
    print("\n[4] RESULT:")
    print(f"    compressed {o_chars} -> {c_chars} chars  "
          f"({o_words} -> {c_words} words),  {pct:.0f}% smaller")
    # This trimmed context is what a real system would splice into the prompt:
    #     # real: llm(f"Answer using only this context:\n{compressed}\n\nQ: {query}")
    return compressed


if __name__ == "__main__":
    # A query about making database / web-app queries faster. Docs 0 and 1 carry
    # the answer (mixed with noise); doc 2 is pure noise and should be filtered.
    contextual_compression(
        "how do I speed up a slow database query in my web app?",
        DOCS,
    )
