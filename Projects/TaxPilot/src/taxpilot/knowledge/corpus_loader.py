"""Parse the corpus markdown into retrievable passages.

Corpus format (one file per topic), e.g. data/corpus/standard-deduction.md:

    # Standard Deduction
    > source: IRS Pub 501 | rules: STD-DED-2024, STD-DED-ADDITIONAL

    ## Basic amount (2024)
    Single filers ...

    ## Additional amount for age or blindness
    ...

The `>` metadata line gives the document source and the rule_ids it documents.
Each `##` heading becomes one passage inheriting that source; text before the
first `##` becomes an intro passage. Keeping one publication topic per file makes
BM25 discriminate cleanly and keeps rule_ids close to the prose they authorise.
"""

from __future__ import annotations

import re
from pathlib import Path

from taxpilot.knowledge.store import Passage

_META = re.compile(r"^>\s*source:\s*(?P<source>[^|]+?)\s*(?:\|\s*rules:\s*(?P<rules>.+))?$")


def parse_file(path: Path) -> list[Passage]:
    lines = path.read_text(encoding="utf-8").splitlines()
    source = ""
    rule_ids: list[str] = []
    body: list[str] = []
    for line in lines:
        meta = _META.match(line.strip())
        if meta:
            source = meta.group("source").strip()
            if meta.group("rules"):
                rule_ids = [r.strip() for r in meta.group("rules").split(",") if r.strip()]
            continue
        # The leading "# Title" is folded into the file's identity, not indexed.
        if line.startswith("# "):
            continue
        body.append(line)

    stem = path.stem
    passages: list[Passage] = []
    for index, (section, text) in enumerate(_split_sections("\n".join(body))):
        clean = text.strip()
        if not clean:
            continue
        passages.append(
            Passage(
                id=f"{stem}#{index}",
                text=clean,
                source=source or stem,
                section=section,
                rule_ids=list(rule_ids),
            )
        )
    return passages


def _split_sections(body: str) -> list[tuple[str, str]]:
    """Split on `##` headings, returning (heading, text) pairs."""
    sections: list[tuple[str, str]] = []
    heading = ""
    buffer: list[str] = []
    for line in body.splitlines():
        if line.startswith("## "):
            if buffer:
                sections.append((heading, "\n".join(buffer)))
            heading = line[3:].strip()
            buffer = []
        else:
            buffer.append(line)
    if buffer:
        sections.append((heading, "\n".join(buffer)))
    return sections


def load_corpus(corpus_dir: Path) -> list[Passage]:
    """Parse every .md file in the corpus directory into passages."""
    passages: list[Passage] = []
    for path in sorted(corpus_dir.glob("*.md")):
        passages.extend(parse_file(path))
    return passages
