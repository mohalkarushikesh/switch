"""
10_parent_document.py -- Small-to-big (parent-document) & sentence-window retrieval.

THE SMALL-vs-BIG TENSION
    You want the chunk you EMBED to be SMALL, so that its vector is about one
    tight idea and matches a query precisely. A big multi-topic paragraph gets a
    "smeared" embedding -- its vector is the average of several ideas, so it
    matches everything a little and nothing sharply.

    But you want the chunk you HAND TO THE LLM to be BIG, because a single lonely
    sentence usually lacks the surrounding context needed to actually answer.
    "Add an index on the filtered column." is a precise match for a slowness
    query, yet on its own the reader does not know WHY or WHEN to do it.

THE FIX: decouple the two.
    - Split each PARENT document (a short multi-sentence paragraph) into small
      CHILD chunks (here: one sentence each).
    - EMBED and RETRIEVE on the small children (precise matching).
    - But RETURN the child's PARENT (full context) to the generator.
    This is "small-to-big" / parent-document retrieval.

    A lighter-weight cousin is the SENTENCE-WINDOW variant: index single
    sentences, and on a hit expand to that sentence PLUS its +/-k neighbours,
    instead of returning the whole parent. Useful when parents are long and you
    only want a local window of context.

Toy pieces: embed()/cosine() from common.py stand in for a real embedding model
and vector store. The "generator" is just a print -- a real system would do
    answer = llm(prompt_with_context)

Run:  python 10_parent_document.py
"""

from common import embed, cosine

# We do NOT use common.CORPUS here: those are single sentences with no parent to
# expand into, so they cannot show the small-vs-big point. We define our own tiny
# STRUCTURED corpus of multi-sentence paragraphs, using words from the embedder's
# SEMANTIC_GROUPS (slow/database/index/caching/latency/python/model/...) so that
# embed() gives real signal.


# --- A structured local corpus: a few multi-sentence PARENT documents --------
# Each parent is a short paragraph on ONE topic. Crucially, the KEY fact lives in
# a different sentence than the general topic sentence -- that is what forces the
# small-vs-big trade-off: the precise sentence matches, but you need its
# neighbours to make sense of it.
PARENTS = [
    # parent 0 -- database performance
    "Database queries can get slow as tables grow. "
    "The usual fix is to add an index on the filtered column. "
    "Without it the database must scan every row on each query.",

    # parent 1 -- web caching
    "Web apps often repeat the same expensive work on every request. "
    "Caching stores a computed response in memory and reuses it. "
    "This cuts response latency dramatically for frequent queries.",

    # parent 2 -- machine learning
    "Python is a popular language for data science work. "
    "Machine learning models learn patterns from large training data. "
    "More clean data usually improves a model more than clever code.",
]

# Give the parents human-readable topic labels (for printing only).
PARENT_TOPICS = ["database-performance", "web-caching", "machine-learning"]

# A deliberately MULTI-TOPIC parent, used only to make the "why embed small, not
# big" point undeniable. Three unrelated sentences (animals / databases / space)
# live in one document. Its averaged embedding is smeared across three different
# meaning groups, so it matches a focused query far worse than the one precise
# child sentence does. Real corpora are full of paragraphs like this.
MIXED_PARENT = (
    "The cat napped on the warm windowsill all afternoon. "
    "To speed up a slow database query, add an index on the filtered column. "
    "The space telescope captured stunning images of distant galaxies."
)


# --- Chunking: split each parent into small CHILD chunks (by sentence) -------
def split_sentences(paragraph):
    """
    Naive sentence splitter: break on '. ' and keep non-empty pieces, re-adding
    the period we split on. A real system would use a proper sentence tokenizer
    (spaCy / nltk) or a token-count-based splitter.
    """
    raw = [s.strip() for s in paragraph.split(". ")]
    out = []
    for s in raw:
        if not s:
            continue
        if not s.endswith("."):
            s = s + "."
        out.append(s)
    return out


# --- Build the child index and the child -> parent mapping -------------------
# This is the heart of parent-document retrieval: we embed the SMALL children,
# but remember which PARENT each child came from (and its position within the
# parent, for the sentence-window variant).
class Child:
    def __init__(self, text, parent_id, sent_index, vec):
        self.text = text            # the small chunk we embed & match on
        self.parent_id = parent_id  # which PARENT document it belongs to
        self.sent_index = sent_index  # position of this sentence inside the parent
        self.vec = vec              # precomputed embedding of the small chunk


def build_index(parents):
    """Split every parent into sentence children and embed each child."""
    # parent_id -> list of that parent's sentences, in order (for windowing).
    parent_sentences = [split_sentences(p) for p in parents]
    children = []
    for parent_id, sentences in enumerate(parent_sentences):
        for sent_index, sent in enumerate(sentences):
            children.append(Child(sent, parent_id, sent_index, embed(sent)))
    return children, parent_sentences


# --- Retrieval: match on the small child, then decide what to RETURN ---------
def best_child(query, children):
    """Return the single child whose small embedding best matches the query."""
    q = embed(query)
    scored = [(c, cosine(q, c.vec)) for c in children]
    scored.sort(key=lambda cs: cs[1], reverse=True)
    return scored[0]  # (Child, score)


def sentence_window(parent_sentences, parent_id, center_index, k=1):
    """
    SENTENCE-WINDOW variant: instead of the whole parent, return the matched
    sentence plus its +/-k neighbours within the same parent. A middle ground
    between "tiny child" and "entire parent".
    """
    sentences = parent_sentences[parent_id]
    lo = max(0, center_index - k)
    hi = min(len(sentences), center_index + k + 1)  # +1: slice end is exclusive
    return " ".join(sentences[lo:hi])


# --- Demo --------------------------------------------------------------------
def demo(query, children, parent_sentences):
    print("\n" + "=" * 74)
    print(f"Query: {query!r}")

    child, score = best_child(query, children)
    parent_text = " ".join(parent_sentences[child.parent_id])

    # 1) What the SMALL child index matched on (precise, but context-starved).
    print("\n[1] Best-matching CHILD chunk (what we retrieved on):")
    print(f"    parent={PARENT_TOPICS[child.parent_id]}  "
          f"sentence#={child.sent_index}  cosine={score:.3f}")
    print(f"    child text : {child.text!r}")
    print("    ^ precise match, but on its own it lacks the surrounding 'why/when'.")

    # 2) Small-to-big: return the FULL PARENT to the generator.
    print("\n[2] What SMALL-TO-BIG returns to the LLM (the whole PARENT):")
    print(f"    {parent_text}")
    print("    ^ same precise hit, now with full context to actually answer.")

    # 3) Sentence-window: a lighter middle ground (+/-1 neighbour).
    window = sentence_window(parent_sentences, child.parent_id,
                             child.sent_index, k=1)
    print("\n[3] What SENTENCE-WINDOW returns instead (matched sentence +/-1):")
    print(f"    {window}")
    print("    ^ local context only -- cheaper than the whole parent when parents are long.")


# --- Why embed SMALL children, not the BIG parent? ---------------------------
def why_embed_small():
    """
    The precision half of the trade-off. A multi-topic parent's embedding is the
    AVERAGE of its sentences, so it is smeared across several meaning groups and
    matches a focused query weakly. The single on-topic child stays sharp. Hence:
    embed the small child (precise recall), but hand back the big parent (context).
    """
    print("\n" + "=" * 74)
    print("WHY EMBED THE SMALL CHILD, NOT THE BIG PARENT?")
    query = "how do I speed up a slow database query with an index?"
    print(f"Query: {query!r}")

    sentences = split_sentences(MIXED_PARENT)
    q = embed(query)

    print("\n  This one parent mixes three unrelated topics:")
    for i, s in enumerate(sentences):
        print(f"    child s{i} cosine={cosine(q, embed(s)):.3f}  {s}")

    child_scores = [cosine(q, embed(s)) for s in sentences]
    best_child_score = max(child_scores)
    parent_score = cosine(q, embed(MIXED_PARENT))

    print(f"\n  best CHILD cosine   = {best_child_score:.3f}  (one sharp, on-topic sentence)")
    print(f"  whole PARENT cosine = {parent_score:.3f}  (averaged/smeared over 3 topics)")
    print("  -> the small child matches MUCH more sharply, so we retrieve on children;")
    print("     we then return the parent only to supply context for the answer.")


if __name__ == "__main__":
    children, parent_sentences = build_index(PARENTS)

    # Sanity: show the child index we built (small chunks + their parent).
    print("Child index (each small chunk knows its parent):")
    for c in children:
        print(f"  [{PARENT_TOPICS[c.parent_id]} s{c.sent_index}] {c.text}")

    # A slowness query: the precise child hit is the TOPIC sentence
    # ("...queries can get slow as tables grow"), but the actual fix -- "add an
    # index" / "scan every row" -- lives in its NEIGHBOURS, which the parent supplies.
    demo("why are my database queries slow and how do I speed them up?",
         children, parent_sentences)

    # A latency query: precise hit is the 'caching stores a response' sentence;
    # the parent supplies the 'cuts response latency' payoff around it.
    demo("how can caching reduce response latency in a web app?",
         children, parent_sentences)

    # The precision half of the story: why we embed the small child at all.
    why_embed_small()
