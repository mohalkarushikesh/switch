"""Load a folder of documents into SourceDocuments and route each by type.

Type routing is a cheap deterministic first pass on the document text and
filename - "Wage and Tax Statement" is a W-2, "Nonemployee compensation" is a
1099-NEC. It only decides which extraction hints apply; the extractor still reads
the actual fields, so a misroute degrades quality rather than producing a wrong
number.
"""

from __future__ import annotations

import logging
from pathlib import Path

from taxpilot.intake.ocr import extract_text
from taxpilot.models import DocType, SourceDocument

logger = logging.getLogger(__name__)

#: (marker, DocType), checked in order against the lowercased text+filename.
#: More specific markers precede the generic ones (Form 16A before Form 16).
_MARKERS: list[tuple[str, DocType]] = [
    ("form 16a", DocType.FORM16A),
    ("form no. 16a", DocType.FORM16A),
    ("form 26as", DocType.FORM26AS),
    ("annual tax statement", DocType.FORM26AS),
    ("form 16", DocType.FORM16),
    ("form no. 16", DocType.FORM16),
    ("certificate under section 203", DocType.FORM16),
    ("rent receipt", DocType.RENT_RECEIPT),
    ("house rent", DocType.RENT_RECEIPT),
    ("section 80c", DocType.INVEST_80C),
    ("80c", DocType.INVEST_80C),
    ("elss", DocType.INVEST_80C),
    ("public provident fund", DocType.INVEST_80C),
    ("section 80d", DocType.MEDICAL_80D),
    ("80d", DocType.MEDICAL_80D),
    ("mediclaim", DocType.MEDICAL_80D),
    ("health insurance", DocType.MEDICAL_80D),
    ("section 80g", DocType.DONATION_80G),
    ("80g", DocType.DONATION_80G),
    ("donation", DocType.DONATION_80G),
    ("home loan", DocType.HOME_LOAN),
    ("housing loan", DocType.HOME_LOAN),
    ("section 24", DocType.HOME_LOAN),
    ("interest certificate", DocType.INTEREST_CERT),
    ("interest income", DocType.INTEREST_CERT),
    ("fixed deposit", DocType.INTEREST_CERT),
]


def classify_doc_type(text: str, filename: str) -> DocType:
    haystack = (filename + "\n" + text[:600]).lower()
    for marker, doc_type in _MARKERS:
        if marker in haystack:
            return doc_type
    return DocType.OTHER


def load_document(path: Path) -> SourceDocument:
    text, confidence = extract_text(path)
    return SourceDocument(
        id=path.stem,
        filename=path.name,
        doc_type=classify_doc_type(text, path.name),
        text=text,
        ocr_confidence=confidence,
    )


def load_documents(directory: Path) -> list[SourceDocument]:
    docs: list[SourceDocument] = []
    for path in sorted(directory.iterdir()):
        if path.is_file():
            try:
                docs.append(load_document(path))
            except Exception:
                logger.exception("Failed to load %s; skipping", path.name)
    return docs
