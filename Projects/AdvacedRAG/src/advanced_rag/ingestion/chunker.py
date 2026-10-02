"""Markdown-aware chunking.

Splitting on headings first keeps a runbook step with its own heading, which is
what makes the citation ("Pod Troubleshooting - CrashLoopBackOff") useful to the
engineer reading the answer. Only oversized sections fall back to a sliding
window over sentence boundaries.
"""

from __future__ import annotations

import hashlib
import re                       # regular expression matching operations
from dataclasses import dataclass

from advanced_rag.models import Chunk

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
_SENTENCE_END = re.compile(r"(?<=[.!?:])\s+|\n\n")


@dataclass
class Section:
    title: str
    body: str


def split_sections(markdown: str) -> list[Section]:
    """
    Reads the markdown document.
    Finds all headings (#, ##, ###, etc.).
    Splits the document into sections.
    Each section contains:
        title = heading text
        body = content under that heading
    """
    
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
    """
    Splits large text into sentences.
    Packs sentences into chunks of maximum size characters.
    Keeps some content (overlap) from the previous chunk in the next chunk for context.
    """
    
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
    """
    Get section title and body.
    Add title at the beginning of every chunk:
        Plain Text
            Pod Troubleshooting
            Check logs...
    If section is too large, use window() to split it.
    Create a Chunk object with:
        unique id
        chunk text
        source file
        title
        section name
        metadata
    Add chunk to the final list.
    """
    
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
    """
    Creates a unique ID using SHA-256 hash.
    
    This ensures:
        Same content → same ID
        Modified content → new ID
    """
    
    """Content-addressed id, so re-ingesting unchanged docs overwrites in place."""
    digest = hashlib.sha256((source + "|" + section + "|" + body).encode()).hexdigest()
    return source + "#" + digest[:16]



"""
Markdown Document
        ↓
split_sections()
        ↓
Section 1, Section 2, ...
        ↓
window() (if section is large)
        ↓
Chunk Objects
        ↓
Unique Hash ID
        ↓
Stored in Vector DB


    - So when retrieved, the LLM gets context + citation source, making answers like: From "Pod Troubleshooting", check container logs using kubectl logs.
"""