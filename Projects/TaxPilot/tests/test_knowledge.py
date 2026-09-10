"""Retrieval surfaces the right section, and every corpus citation resolves."""

from taxpilot.config import get_settings
from taxpilot.knowledge import format_context, is_known
from taxpilot.knowledge.corpus_loader import load_corpus
from taxpilot.knowledge.retriever import Retriever


def _retriever():
    return Retriever(get_settings())


def test_corpus_loads():
    settings = get_settings()
    passages = load_corpus(settings.absolute(settings.corpus_dir))
    assert len(passages) >= 8


def test_every_corpus_rule_id_is_in_the_catalog():
    settings = get_settings()
    for passage in load_corpus(settings.absolute(settings.corpus_dir)):
        for rule_id in passage.rule_ids:
            assert is_known(rule_id), rule_id


def test_retrieval_finds_the_expected_section():
    retriever = _retriever()
    cases = {
        "standard deduction on salary": "SALARY-STD-DED",
        "section 80C investment deduction limit": "80C",
        "home loan interest self occupied section 24": "SEC24B",
        "new regime tax slabs 2024": "SLAB-NEW-2024",
        "rebate under section 87A": "REBATE-87A",
    }
    for query, expected in cases.items():
        hits = retriever.retrieve(query, top_k=3)
        assert hits, query
        found = {r for hit in hits for r in hit.passage.rule_ids}
        assert expected in found, f"{query!r} -> {found}"


def test_format_context_names_rule_ids():
    retriever = _retriever()
    hits = retriever.retrieve("section 80C deduction", top_k=2)
    context = format_context([h.passage for h in hits])
    assert "rule_ids:" in context
    assert "80C" in context
