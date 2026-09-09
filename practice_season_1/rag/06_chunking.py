"""
06_chunking.py -- Chunking strategies: HOW you split docs drives retrieval.

You almost never embed a whole document. You SPLIT it into chunks, embed each
chunk, and retrieve chunks. That splitting step is not a boring preprocessing
detail -- it silently decides what a retriever can and cannot find:

    too SMALL  -> a single idea gets torn across two chunks; neither chunk on
                  its own answers the query (lost context).
    too BIG    -> one chunk mixes many topics; its embedding is an averaged blur
                  that matches everything weakly and nothing strongly (dilution).
    OVERLAP    -> let consecutive chunks share a few words, so an idea that
                  straddles a boundary survives INTACT inside at least one chunk
                  (safer, at the cost of some redundant/duplicated text).

This file builds its OWN short sample paragraph (the shared 10-doc corpus is one
sentence per doc, too short to show a split). The paragraph is written using the
toy embedder's known vocabulary (slow, sluggish, database, query, index,
caching, latency, web app, python, machine learning...) so embed() gives real
signal in the payoff at the end.

We demonstrate three strategies, print their chunks, then show the payoff: a
query whose answer sits ON a chunk boundary is retrieved by the OVERLAP chunks
but split (and weakened) by the NO-OVERLAP chunks.

The embedder (embed/cosine) is the same toy stand-in as the other demos; a real
system would call a sentence-embedding model here.

Run:  python 06_chunking.py
"""

import re
from common import embed, cosine


# --- The sample document ----------------------------------------------------
# One short paragraph about database performance, deliberately worded with the
# toy embedder's vocabulary so embed() has signal. The KEY sentence for the
# payoff is "...feel slow and sluggish. The database query behind it scans a
# full table..." -- the *problem* (slow/sluggish) and the *subject* (database
# query) sit next to each other, so a chunk boundary dropped between them splits
# one idea in half.
DOC = (
    "Python trains machine learning models on training data. "
    "Our web app started to feel slow and sluggish. "
    "The database query behind it scans a full table. "
    "Adding an index on that column speeds the query. "
    "Caching cached results in memory cuts response latency."
)


# --- Strategy 1: fixed-size, NO overlap -------------------------------------
def fixed_chunks(text, size):
    """
    Cut the text into back-to-back blocks of `size` words. Dead simple and cheap,
    but the knife falls at a fixed word count with no regard for meaning -- so it
    happily slices through the middle of a sentence or idea.
    """
    words = text.split()
    return [" ".join(words[i:i + size]) for i in range(0, len(words), size)]


# --- Strategy 2: fixed-size WITH overlap (sliding window) -------------------
def sliding_chunks(text, size, overlap):
    """
    Same fixed width, but each window starts `size - overlap` words after the
    previous one, so neighbouring chunks SHARE `overlap` words. An idea that
    lands on a boundary now appears whole inside at least one window. Cost: the
    shared words are stored/embedded more than once (redundancy).
    """
    words = text.split()
    step = size - overlap                       # how far the window advances
    assert step > 0, "overlap must be smaller than size"
    chunks = []
    for i in range(0, len(words), step):
        chunk = words[i:i + size]
        chunks.append(" ".join(chunk))
        if i + size >= len(words):              # last window reached the end; stop
            break
    return chunks


# --- Strategy 3: sentence-based (respect natural boundaries) ----------------
def sentence_chunks(text, budget):
    """
    Split on sentence boundaries first, then PACK whole sentences together until
    adding the next one would blow a `budget` (in words). This never cuts a
    sentence in half, so each chunk is a self-contained thought -- usually the
    best default for prose. Chunk sizes vary because sentences vary.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())   # keep the terminator
    chunks, cur, cur_len = [], [], 0
    for s in sentences:
        n = len(s.split())
        if cur and cur_len + n > budget:        # would overflow -> seal current chunk
            chunks.append(" ".join(cur))
            cur, cur_len = [], 0
        cur.append(s)
        cur_len += n
    if cur:
        chunks.append(" ".join(cur))
    return chunks


# --- Small helpers for display + retrieval ----------------------------------
def show_chunks(title, chunks):
    print("\n" + title)
    for i, c in enumerate(chunks):
        print(f"  [{i}] ({len(c.split())}w)  {c}")


def rank_chunks(query, chunks):
    """Embed the query and every chunk, return (index, cosine, text) best-first."""
    q = embed(query)                            # real: model.encode(query)
    scored = [(i, cosine(q, embed(c)), c) for i, c in enumerate(chunks)]
    return sorted(scored, key=lambda x: x[1], reverse=True)


def show_ranking(title, ranking, topn=3):
    print("\n" + title)
    for rank, (idx, score, text) in enumerate(ranking[:topn], start=1):
        print(f"  {rank}. score={score:.3f}  [{idx}]  {text}")


if __name__ == "__main__":
    print("=== SAMPLE DOCUMENT (" + str(len(DOC.split())) + " words) ===")
    print(DOC)

    # -- Show the three strategies side by side -----------------------------
    SIZE = 6                                    # words per fixed-size chunk

    no_overlap = fixed_chunks(DOC, SIZE)
    overlap = sliding_chunks(DOC, SIZE, overlap=3)     # 50% sliding window
    by_sentence = sentence_chunks(DOC, budget=12)

    print("\n\n=== STRATEGY 1: fixed-size, NO overlap (size=6) ===")
    print("Note chunk [2] ends '...slow and sluggish. The' and chunk [3] starts")
    print("'database query ...': the PROBLEM (slow/sluggish) and its SUBJECT")
    print("(database query) got torn apart at the boundary.")
    show_chunks("chunks:", no_overlap)

    print("\n\n=== STRATEGY 2: fixed-size WITH overlap (size=6, overlap=3) ===")
    print("Windows share 3 words, so at least one chunk keeps 'sluggish ... The")
    print("database query' together -- the straddling idea survives intact.")
    show_chunks("chunks:", overlap)

    print("\n\n=== STRATEGY 3: sentence-based, packed to a 12-word budget ===")
    print("Never cuts a sentence; each chunk is a whole thought (sizes vary).")
    show_chunks("chunks:", by_sentence)

    # -- The payoff: a query whose answer sits ON a boundary ----------------
    # The user is describing a slow database query. Answering needs BOTH the
    # slowness words (dim "slowness") and the database words (dim "databases")
    # in the SAME chunk. No-overlap put them in different chunks; overlap didn't.
    query = "slow sluggish database query"
    print("\n\n=== PAYOFF: retrieve for query " + repr(query) + " ===")
    print("The answer lives right on the chunk boundary, so it needs the slowness")
    print("words AND the database words together in one chunk to score well.")

    r_no = rank_chunks(query, no_overlap)
    r_ov = rank_chunks(query, overlap)

    show_ranking("NO-OVERLAP retrieval -- best chunk is only HALF the idea:", r_no)
    show_ranking("OVERLAP retrieval -- best chunk has the WHOLE idea:", r_ov)

    best_no = r_no[0][1]
    best_ov = r_ov[0][1]
    print("\n--- Verdict ------------------------------------------------------")
    print(f"  no-overlap best cosine = {best_no:.3f}  (a fragment: slowness OR")
    print("                                 database, never both -> ~0.71 = a")
    print("                                 45-degree miss on the query)")
    print(f"  overlap    best cosine = {best_ov:.3f}  (the boundary-spanning chunk")
    print("                                 ties slowness TO the database query)")
    print(f"  overlap wins by {best_ov - best_no:+.3f} cosine on the exact chunk")
    print("  that actually answers the question.")

    # -- Trade-offs, made concrete ------------------------------------------
    print("\n--- Trade-offs ---------------------------------------------------")
    # Too big: embed the whole paragraph as ONE chunk -> topic soup.
    whole = cosine(embed(query), embed(DOC))
    print(f"  too BIG   : whole doc as 1 chunk scores {whole:.3f} vs the focused")
    print("              overlap chunk's %.3f -- one giant chunk mixes python, ML," % best_ov)
    print("              caching and DB, so its embedding is a diluted blur.")
    print("  too SMALL : size=1 or 2 words would split 'database query' itself,")
    print("              losing the phrase's meaning entirely (lost context).")
    print("  OVERLAP   : safest for boundary-spanning ideas, but the shared words")
    print("              are embedded/stored twice -- redundancy costs space and")
    print("              can return near-duplicate chunks. Pick overlap ~10-20%")
    print("              in practice; we used 50% here to make the point loud.")
