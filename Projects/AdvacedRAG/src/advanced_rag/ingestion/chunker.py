"""Markdown-aware chunking.

Splitting on headings first keeps a runbook step with its own heading, which is
what makes the citation ("Pod Troubleshooting - CrashLoopBackOff") useful to the
engineer reading the answer. Only oversized sections fall back to a sliding
window over sentence boundaries.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from advanced_rag.models import Chunk

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
_SENTENCE_END = re.compile(r"(?<=[.!?:])\s+|\n\n")


@dataclass
class Section:
    title: str
    body: str


def split_sections(markdown: str) -> list[Section]:
    """Break a document at its headings, keeping each heading with its body."""
    matches = list(_HEADING.finditer(markdown))
    if not matches:
        return [Section(title="", body=markdown.strip())]

    sections: list[Section] = []
    preamble = markdown[: matches[0].start()].strip()
    if preamble:
        sections.append(Section(title="", body=preamble))

    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        body = markdown[match.end() : end].strip()
        if body:
            sections.append(Section(title=match.group(2).strip(), body=body))
    return sections


def window(text: str, size: int, overlap: int) -> list[str]:
    """Pack sentences into <=`size` character windows that overlap by `overlap`."""
    pieces = [p.strip() for p in _SENTENCE_END.split(text) if p.strip()]
    if not pieces:
        return []

    windows: list[str] = []
    current: list[str] = []
    length = 0
    for piece in pieces:
        if length + len(piece) > size and current:
            windows.append(" ".join(current))
            # Re-seed the next window with the tail of this one.
            tail: list[str] = []
            tail_length = 0
            for previous in reversed(current):
                if tail_length + len(previous) > overlap:
                    break
                tail.insert(0, previous)
                tail_length += len(previous)
            current, length = tail, tail_length
        current.append(piece)
        length += len(piece)
    if current:
        windows.append(" ".join(current))
    return windows


def chunk_document(
    *,
    text: str,
    source: str,
    title: str,
    doc_type: str = "runbook",
    metadata: dict | None = None,
    chunk_size: int = 900,
    chunk_overlap: int = 150,
) -> list[Chunk]:
    """Turn one markdown document into retrievable chunks."""
    chunks: list[Chunk] = []
    for section in split_sections(text):
        # Prefixing the section title gives the embedding local context that the
        # body alone often lacks (bare command blocks, bullet fragments).
        prefix = section.title + "\n" if section.title else ""
        for part in window(section.body, chunk_size, chunk_overlap) or [section.body]:
            body = (prefix + part).strip()
            if len(body) < 40:
                continue
            chunks.append(
                Chunk(
                    id=_chunk_id(source, section.title, body),
                    text=body,
                    source=source,
                    title=title,
                    section=section.title,
                    doc_type=doc_type,
                    metadata=dict(metadata or {}),
                )
            )
    return chunks


def _chunk_id(source: str, section: str, body: str) -> str:
    """Content-addressed id, so re-ingesting unchanged docs overwrites in place."""
    digest = hashlib.sha256((source + "|" + section + "|" + body).encode()).hexdigest()
    return source + "#" + digest[:16]
