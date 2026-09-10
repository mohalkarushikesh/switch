"""Field extraction from one document.

The LLM path reads messy, real-world text and returns fields with per-field
confidence - that is the job a model is genuinely good at. The heuristic path
parses the clean "Label: amount" layout of the sample documents with regex and no
model at all, so the whole pipeline runs, and the whole test suite passes, with no
API key or network. The extractor falls back to the heuristic automatically when
the model is unavailable, and either way the labels are canonicalized to the same
field names before anything downstream sees them.
"""

from __future__ import annotations

import logging
import re

from pydantic import BaseModel, Field

from taxpilot.extraction.schema import canonicalize
from taxpilot.llm import prompts
from taxpilot.llm.client import LLMClient
from taxpilot.models import ExtractedField, ExtractionResult, SourceDocument

logger = logging.getLogger(__name__)

#: "Gross salary: 14,00,000" / "Amount: Rs 1,50,000". An optional "Item N - "
#: prefix is stripped, the label runs up to the colon (so commas and parentheses
#: inside a label are fine), and the value is the rest.
_LINE = re.compile(r"^\s*(?:box\s*\S+\s*[-:]\s*)?(?P<label>[A-Za-z][^:]*?)\s*:\s*"
                   r"(?P<value>.+?)\s*$", re.I)
#: A leading currency amount, allowing a rupee/Rs/INR/$ prefix and accounting
#: parentheses. Not end-anchored, so "1,50,000 (see annexure)" reads as a number -
#: but a value whose number is immediately followed by "-" or "/" (a dashed
#: identifier like a PAN date, or a slash date) is left as a string by _coerce.
_NUMBER = re.compile(r"^\(?\s*(?:₹|rs\.?|inr|\$)?\s*-?\s*(?P<num>[\d,]+(?:\.\d+)?)", re.I)


# ---- LLM output schema (kept internal; converted to ExtractedField afterwards)


class _RawField(BaseModel):
    label: str = Field(description="the field name or box label as printed")
    value: str = Field(description="the value exactly as printed, verbatim")
    confidence: float = Field(description="0..1 confidence this was read correctly")
    box: str = Field(description="the box/line it came from, or ''")


class _RawExtraction(BaseModel):
    fields: list[_RawField]


class Extractor:
    def __init__(self, llm: LLMClient | None) -> None:
        self.llm = llm

    def extract(self, doc: SourceDocument) -> ExtractionResult:
        raw = self._extract_llm(doc) if self.llm is not None else None
        if raw is None:
            raw = self._extract_heuristic(doc)
        return ExtractionResult(doc_id=doc.id, doc_type=doc.doc_type, fields=raw)

    # ------------------------------------------------------------------ LLM

    def _extract_llm(self, doc: SourceDocument) -> list[ExtractedField] | None:
        prompt = f"Document type (as routed): {doc.doc_type.value}\n\nText:\n{doc.text}"
        try:
            result = self.llm.complete_json(prompt, _RawExtraction, system=prompts.EXTRACTOR_SYSTEM)
        except Exception as exc:
            logger.warning("LLM extraction failed for %s, using heuristic: %s", doc.id, exc)
            return None
        fields: list[ExtractedField] = []
        for item in result.fields:
            fields.append(ExtractedField(
                name=canonicalize(item.label),
                value=_coerce(item.value),
                confidence=_clamp(item.confidence),
                source_doc=doc.id,
                box=item.box,
            ))
        return fields

    # ------------------------------------------------------------ heuristic

    def _extract_heuristic(self, doc: SourceDocument) -> list[ExtractedField]:
        fields: list[ExtractedField] = []
        for line in doc.text.splitlines():
            match = _LINE.match(line)
            if not match:
                continue
            label = match.group("label")
            value = _coerce(match.group("value"))
            # A clean born-digital document reads with high confidence; OCR'd text
            # inherits the page's OCR confidence so downstream flagging still works.
            confidence = 0.95 if doc.ocr_confidence is None else _clamp(doc.ocr_confidence)
            fields.append(ExtractedField(
                name=canonicalize(label), value=value, confidence=confidence, source_doc=doc.id,
            ))
        return fields


def _coerce(value: str) -> float | str:
    """Numbers become floats (drop $ and thousands commas); everything else stays text.

    A number carrying trailing noise ("1,50,000 (see annexure)") is still read -
    OCR output routinely appends footnote markers. But a number that is really the
    start of a separated identifier or date ("15/04/2024", a PAN date) is left as
    text. The guard fires only when the "-"/"/" is followed by another digit, so
    the ubiquitous Indian rupee suffix "1,50,000/-" is read as 150000, not dropped.
    """
    text = value.strip()
    match = _NUMBER.match(text)
    if not match:
        return text
    tail = text[match.end():match.end() + 2]
    if tail[:1] in ("-", "/") and tail[1:2].isdigit():  # a date/identifier, not "/-"
        return text
    number = float(match.group("num").replace(",", ""))
    if text.startswith("(") or text.lstrip().startswith("-"):
        number = -number
    return number


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
