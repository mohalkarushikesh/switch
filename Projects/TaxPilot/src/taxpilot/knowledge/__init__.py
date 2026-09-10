"""IRS-rule knowledge base: a BM25 index over publication excerpts, plus the
rule catalog that every citation resolves against."""

from taxpilot.knowledge.retriever import (
    Retriever,
    format_context,
    get_retriever,
    reset_retriever,
)
from taxpilot.knowledge.rules import RULES, cite, is_known

__all__ = [
    "Retriever",
    "format_context",
    "get_retriever",
    "reset_retriever",
    "RULES",
    "cite",
    "is_known",
]
