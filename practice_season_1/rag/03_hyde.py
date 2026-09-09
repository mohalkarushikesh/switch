"""
03_hyde.py -- HyDE: Hypothetical Document Embeddings.

The problem: a user's query and the documents that answer it are often written
very differently. A short, vague question ("my site feels janky") shares almost
no vocabulary with the passage that answers it ("...high latency... add
caching..."). Embedding the raw query lands it in the wrong neighbourhood -- or,
if none of its words are known, gives no usable signal at all.

HyDE's trick (Gao et al., 2022):
    1. Ask an LLM to WRITE a hypothetical answer to the query. It will be
       partly wrong -- that's fine, we never show it to the user.
    2. Embed that hypothetical ANSWER instead of the raw query.
    3. Retrieve with that embedding. A fake-but-plausible answer looks a lot
       like the real answer documents, so it lands near them.

We're trading "query looks like answers?" (often no) for "answer looks like
answers?" (usually yes).

The LLM call is faked with keyword-triggered templates. A REAL system does:
    hypothetical = llm(f"Write a short passage that answers: {query}")

Run:  python 03_hyde.py
"""

from common import CORPUS, embed, embed_corpus, cosine, tokenize


# --- Fake LLM: generate a hypothetical answer -------------------------------
# A real LLM writes this free-form. Offline, we detect a rough topic from the
# query and return a canned passage that reads like a real answer would -- rich
# in the domain vocabulary that the terse query was missing.
KNOWLEDGE = {
    "performance": (
        "A slow or unresponsive website is usually caused by high latency and "
        "missing caching. Optimizing database queries, adding an index, and "
        "caching frequent responses can speed up a sluggish web app."
    ),
    "animals": (
        "Cats and dogs are common household pets. Dogs enjoy playing fetch at "
        "the park, while a cat is happy to nap in a warm spot."
    ),
    "health": (
        "Good health comes from a balanced diet of vegetables, fruits and lean "
        "protein, plus regular exercise to improve cardiovascular fitness."
    ),
}

# Surface words that hint at each topic (a real LLM needs no such crutch).
TOPIC_HINTS = {
    "performance": {"site", "website", "slow", "laggy", "janky", "unresponsive",
                    "fast", "speed", "latency", "database", "query", "app", "web", "load"},
    "animals": {"cat", "dog", "pet", "animal", "puppy", "kitten"},
    "health": {"diet", "exercise", "healthy", "fitness", "nutrition", "workout"},
}


def hypothetical_answer(query):
    q = set(tokenize(query))
    for topic, hints in TOPIC_HINTS.items():
        if q & hints:
            return KNOWLEDGE[topic]
    return "This is a general topic with no specific detail available."   # fallback


def rank(vector, doc_vecs):
    scored = [(i, cosine(vector, dv)) for i, dv in enumerate(doc_vecs)]
    return sorted(scored, key=lambda x: x[1], reverse=True)


def show(title, ranking, topn=3):
    print("\n" + title)
    for r, (doc_id, score) in enumerate(ranking[:topn], start=1):
        print(f"  {r}. (score={score:.4f})  {CORPUS[doc_id]}")


if __name__ == "__main__":
    # Deliberately vague, using words that appear in NO document.
    query = "my site feels janky and unresponsive"
    print(f"Query: {query!r}")

    doc_vecs = embed_corpus()

    # Baseline: embed the raw query. Its words ("site", "janky"...) aren't in any
    # document's vocabulary, so the embedding is empty -> every score is 0.0.
    show("Retrieval with the RAW query embedding (no usable signal):",
         rank(embed(query), doc_vecs))

    # HyDE: generate a hypothetical answer, then embed THAT.
    hypo = hypothetical_answer(query)
    print(f"\nHyDE step -- LLM's hypothetical answer:\n  {hypo!r}")

    show("Retrieval with the HYPOTHETICAL answer's embedding (now it finds the perf docs):",
         rank(embed(hypo), doc_vecs))
