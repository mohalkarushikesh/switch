"""Load the document corpus from disk.

Documents are markdown with a small YAML-ish front matter block. Front matter is
parsed with a hand-rolled reader rather than pulling in PyYAML: the schema is
five flat string keys and nothing more is needed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from advanced_rag.config import get_settings
from advanced_rag.ingestion.chunker import chunk_document
from advanced_rag.models import Chunk

logger = logging.getLogger(__name__)

CORPUS_DIR = Path("data/corpus")

#: Front matter keys promoted to first-class chunk fields; the rest become metadata.
_RESERVED = {"title", "doc_type"}


@dataclass
class Document:
    source: str
    title: str
    body: str
    doc_type: str = "runbook"
    metadata: dict[str, str] = field(default_factory=dict)


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Split a leading `---` fenced block into a flat dict plus the remaining body."""
    if not text.startswith("---"):
        return {}, text

    lines = text.splitlines()
    closing = next((i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---"), None)
    if closing is None:
        return {}, text

    meta: dict[str, str] = {}
    for line in lines[1:closing]:
        if not line.strip() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip("\"'")
    return meta, "\n".join(lines[closing + 1 :]).lstrip()


def load_document(path: Path, *, root: Path | None = None) -> Document:
    raw = path.read_text(encoding="utf-8")
    meta, body = parse_front_matter(raw)
    source = path.relative_to(root).as_posix() if root else path.name
    return Document(
        source=source,
        title=meta.get("title") or path.stem.replace("-", " ").title(),
        body=body,
        doc_type=meta.get("doc_type", "runbook"),
        metadata={k: v for k, v in meta.items() if k not in _RESERVED},
    )


def load_corpus(directory: Path | None = None) -> list[Document]:
    settings = get_settings()
    root = settings.absolute(directory or CORPUS_DIR)
    if not root.exists():
        raise FileNotFoundError(f"corpus directory not found: {root}")

    paths = sorted(root.rglob("*.md"))
    if not paths:
        raise FileNotFoundError(f"no markdown documents under {root}")
    logger.info("Loaded %d documents from %s", len(paths), root)
    return [load_document(path, root=root) for path in paths]


def chunk_corpus(documents: list[Document]) -> list[Chunk]:
    settings = get_settings()
    chunks: list[Chunk] = []
    for document in documents:
        produced = chunk_document(
            text=document.body,
            source=document.source,
            title=document.title,
            doc_type=document.doc_type,
            metadata=document.metadata,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        logger.info("%s -> %d chunks", document.source, len(produced))
        chunks.extend(produced)
    return chunks
