"""
11_multi_hop.py -- Multi-hop / iterative retrieval.

Some questions cannot be answered by a SINGLE retrieval, because the answer is
spread across several documents that must be CHAINED together:

    Q: "Who leads the team that owns the Switch service?"

No single fact says "X leads the team that owns Switch". You must:
    hop 1 : find WHICH TEAM owns the Switch service          -> "Payments team"
    hop 2 : find WHO LEADS that team                          -> "Dana Reyes"

A one-shot retriever grabs the doc that looks most like the whole question and
stops -- so it returns a fact about ownership OR leadership, never the bridge
between them, and the real answer never surfaces.

Multi-hop (a.k.a. iterative / recursive) retrieval fixes this with a LOOP:
    1. retrieve for the current sub-question,
    2. EXTRACT the intermediate entity from the top fact,
    3. REFORMULATE the next sub-question using that entity,
    4. retrieve again -- repeat until we have the final answer (or hit a cap).

The entities here (service names, team names, people) are NOT in the toy
SEMANTIC_GROUPS in common.py, so embed()/cosine() would give no signal. For
named-entity chaining like this the right tool is a LEXICAL retriever: score
each doc by how many query terms it contains verbatim. We build that from the
shared tokenize()/STOPWORDS helpers.

The extractor and query-reformulator below are clearly-labelled TOY STUBS; a
real system would ask an LLM to read the retrieved fact and emit the entity /
the next question. Where that call goes is marked with "# real: llm(...)".

Run:  python 11_multi_hop.py
"""

from common import tokenize, STOPWORDS


# --- A tiny local knowledge base --------------------------------------------
# The two facts needed for the chain are deliberately kept in SEPARATE docs, so
# that answering requires two hops. The rest are DISTRACTORS: they mention the
# same surface words ("team", "service", "Switch", "leads") to tempt a lexical
# retriever into the wrong doc, exactly like noisy real corpora do.
KB = [
    "The Switch service is owned by the Payments team.",              # 0  hop-1 fact
    "The Payments team is led by Dana Reyes.",                        # 1  hop-2 fact
    "The Switch service processes internal money transfers.",         # 2  distractor (about Switch, no ownership)
    "The Ledger service is owned by the Accounting team.",            # 3  distractor (different service)
    "The Accounting team is led by Sam Okafor.",                      # 4  distractor (different team's leader)
    "Dana Reyes joined the company in 2019 as an engineer.",          # 5  distractor (about the person)
    "The Payments team runs the on-call rotation every weekend.",     # 6  distractor (mentions team, not its lead)
]


# --- Lexical retriever -------------------------------------------------------
# Score each doc by how many of the query's CONTENT words it contains verbatim.
# We drop stopwords so tiny words ("the", "who", "that") don't dominate, and we
# match on unique query terms so a doc cannot win just by repeating one word.
def lexical_score(query, doc):
    q = [t for t in tokenize(query) if t not in STOPWORDS]
    if not q:
        return 0.0
    d = set(tokenize(doc))
    return sum(1 for t in set(q) if t in d) / len(set(q))


def retrieve(query, k=1):
    """Return the top-k (doc_id, score) lexical hits, best first."""
    scored = [(i, lexical_score(query, doc)) for i, doc in enumerate(KB)]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]


# --- TOY extractor: pull the "answer entity" out of a retrieved fact --------
# A real system would ask an LLM, e.g.:
#     # real: llm(f"From this fact, extract the {want}: {fact}")
# We fake it with a couple of hand-written surface patterns keyed on WHAT we are
# looking for ("team" vs "person"). This is intentionally dumb -- the teaching
# point is the retrieve -> extract -> reformulate LOOP, not the parser.
def extract_entity(fact, want):
    words = fact.rstrip(".").split()
    if want == "team":
        # ".. owned by the Payments team." -> the word right before "team".
        if "team" in words:
            i = words.index("team")
            if i > 0:
                return words[i - 1] + " team"
    if want == "person":
        # ".. is led by Dana Reyes." -> everything after "by".
        if "by" in words:
            return " ".join(words[words.index("by") + 1:])
    return None


# --- TOY query reformulator --------------------------------------------------
# Given the entity we just extracted, phrase the NEXT sub-question. A real system
# would let the LLM plan this next step:
#     # real: llm(f"Given we learned '{entity}', what should we ask next?")
def reformulate(entity):
    # Phrase it to echo the KB's own wording ("led by") so the lexical retriever
    # lands on the leadership fact rather than tying with the ownership fact --
    # a real LLM reformulator would likewise adapt phrasing to the corpus.
    return f"Who is the {entity} led by?"


# --- Single-shot baseline (what we are improving on) ------------------------
def single_shot(question):
    print("=== Single-shot retrieval (one query, no chaining) ===")
    print(f"  question: {question!r}")
    doc_id, score = retrieve(question, k=1)[0]
    print(f"  top fact (score={score:.2f}): {KB[doc_id]}")
    print("  -> This fact does not contain a PERSON, so the question is unanswered.")
    print("     One retrieval can match ownership OR leadership -- never the bridge.\n")


# --- Multi-hop loop ----------------------------------------------------------
def multi_hop(question, max_hops=3):
    print("=== Multi-hop retrieval (retrieve -> extract -> reformulate -> repeat) ===")
    print(f"  original question: {question!r}\n")

    # Hop 1 always starts from the original question, asking for the bridge
    # entity (the team that owns the service). Later hops ask for the person.
    sub_q = question
    want = "team"          # what the extractor should pull out on this hop
    answer = None

    for hop in range(1, max_hops + 1):
        doc_id, score = retrieve(sub_q, k=1)[0]
        fact = KB[doc_id]
        entity = extract_entity(fact, want)

        print(f"  hop {hop}:")
        print(f"    sub-question : {sub_q!r}")
        print(f"    retrieved    : (score={score:.2f}) {fact}")
        print(f"    extracted    : {entity!r}  (looking for a {want})")

        if want == "person":
            # We just resolved the leader -> that is the final answer. Stop.
            answer = entity
            print(f"    -> final entity found, stopping.\n")
            break

        # Otherwise we found the bridge entity (the team); reformulate and loop.
        sub_q = reformulate(entity)
        want = "person"
        print(f"    -> reformulated next sub-question: {sub_q!r}\n")

    if answer:
        print(f"  COMPOSED ANSWER: {answer} leads the team that owns the Switch service.")
    else:
        print(f"  Gave up after {max_hops} hops without a final answer.")


if __name__ == "__main__":
    question = "Who leads the team that owns the Switch service?"

    # 1) The naive approach: one retrieval, which structurally cannot answer.
    single_shot(question)

    # 2) Chaining facts across two hops recovers the true answer.
    multi_hop(question)
