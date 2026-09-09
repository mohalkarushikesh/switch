"""
common.py -- shared toy pieces for the RAG concept demos.

Everything here is a *stand-in* for the heavy machinery a real RAG system uses:

    TinyEmbedder (embed)  ~  a real sentence-embedding model (e.g. a sentence-transformer)
    CORPUS                ~  your vector store / document collection
    tokenize              ~  a real tokenizer

The point of these demos is the RETRIEVAL LOGIC layered on top (hybrid search,
reranking, HyDE, CRAG, Self-RAG), not the embedder. So the embedder is
deliberately tiny, deterministic and offline -- no models to download, runs
anywhere with just numpy. Where a real model/LLM would go, a comment says so.
"""

import re
import numpy as np


# --- A small, shared document collection ------------------------------------
# Ten short, single-sentence "documents" spanning a few clearly different topics
# (animals, database performance, web caching, programming, space, health).
# Small enough to reason about by eye; varied enough that retrieval is non-trivial.
CORPUS = [
    "The cat napped on the warm windowsill all afternoon.",                         # 0 animals
    "Dogs are loyal pets that love playing fetch at the park.",                     # 1 animals
    "To speed up a slow database query, add an index on the filtered column.",      # 2 db perf (keyword-heavy)
    "Optimizing sluggish SQL performance usually means avoiding full table scans.", # 3 db perf (paraphrase)
    "Caching frequent results can dramatically cut response latency in web apps.",  # 4 web / caching
    "Python is a popular programming language for data science and machine learning.",  # 5 programming
    "Machine learning models learn patterns from large amounts of training data.",  # 6 ML
    "The space telescope captured stunning images of distant galaxies.",            # 7 space
    "A balanced diet of vegetables, fruits, and lean protein supports good health.",# 8 health
    "Regular exercise improves cardiovascular fitness and lowers stress.",          # 9 health
]


def tokenize(text):
    """Lowercase and split into word tokens, dropping punctuation."""
    return re.findall(r"[a-z0-9]+", text.lower())


# A handful of common words that carry little topical meaning. Real systems use
# a curated stopword list; this is just enough for the demos.
STOPWORDS = {
    "how", "do", "i", "the", "a", "an", "to", "is", "are", "of", "in", "on",
    "my", "can", "what", "s", "and", "for", "with", "should", "this", "that",
    "it", "you", "me", "up", "by", "or", "be", "if", "so", "then", "which",
    "at", "your", "from", "usually", "means", "does", "will", "some",
}


def content_tokens(text):
    """Tokens that actually carry meaning (stopwords removed)."""
    return [t for t in tokenize(text) if t not in STOPWORDS]


# --- A tiny "semantic" embedder ---------------------------------------------
# A real embedder maps text into a few hundred/thousand LEARNED dimensions where
# synonyms land near each other. We fake that with a handful of hand-made
# "meaning groups": each group is one dimension of the vector, and a word bumps
# the dimension of every group it belongs to. Words that share a group (e.g.
# "slow" / "sluggish" / "latency") therefore produce similar vectors -- that is
# the semantic behaviour dense retrieval relies on. Unknown words add nothing to
# the vector (dense retrieval is about topic, not exact spelling).
SEMANTIC_GROUPS = [
    {"slow", "sluggish", "lag", "laggy", "latency", "delay"},                                   # 0 slowness
    {"fast", "faster", "speed", "speedup", "optimize", "optimizing", "accelerate", "quick"},    # 1 speed
    {"database", "db", "sql", "query", "queries", "table", "tables", "index", "scan", "scans"}, # 2 databases
    {"cache", "caching", "cached", "memory", "response", "web", "app", "apps", "website"},       # 3 web/caching
    {"cat", "cats", "dog", "dogs", "pet", "pets", "fetch", "park", "nap", "napped"},             # 4 animals
    {"space", "telescope", "galaxy", "galaxies", "star", "stars", "images"},                     # 5 space
    {"health", "healthy", "diet", "exercise", "fitness", "nutrition", "protein",
     "vegetables", "fruits", "cardiovascular", "stress"},                                        # 6 health
    {"python", "programming", "language", "code", "coding", "software"},                         # 7 programming
    {"machine", "learning", "model", "models", "data", "training", "patterns"},                  # 8 ML
]

# Reverse lookup: word -> list of group dimensions it belongs to.
_WORD_TO_DIMS = {}
for _dim, _group in enumerate(SEMANTIC_GROUPS):
    for _word in _group:
        _WORD_TO_DIMS.setdefault(_word, []).append(_dim)


def embed(text):
    """
    Turn text into an L2-normalized "semantic" vector (one dimension per group).

    A REAL system would call an embedding model here, e.g.:
        vec = sentence_transformer.encode(text)
    """
    vec = np.zeros(len(SEMANTIC_GROUPS), dtype=float)
    for token in tokenize(text):
        for dim in _WORD_TO_DIMS.get(token, ()):   # unknown words contribute nothing
            vec[dim] += 1.0
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec          # avoid divide-by-zero on empty vecs


def cosine(a, b):
    """Cosine similarity in [0, 1] here; returns 0 if either vector is all zeros."""
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def embed_corpus(corpus=CORPUS):
    """Pre-embed every document. A real system stores these vectors in a vector DB."""
    return [embed(doc) for doc in corpus]


def lexical_coverage(query, doc):
    """Fraction of the query's *content* words that appear verbatim in the doc."""
    q = content_tokens(query)
    if not q:
        return 0.0
    d = set(tokenize(doc))
    return sum(1 for t in q if t in d) / len(q)
