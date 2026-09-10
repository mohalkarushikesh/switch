"""Document intake: read files (OCR when needed) and route them by type."""

from taxpilot.intake.loader import classify_doc_type, load_document, load_documents
from taxpilot.intake.ocr import OcrUnavailableError, extract_text

__all__ = [
    "load_documents",
    "load_document",
    "classify_doc_type",
    "extract_text",
    "OcrUnavailableError",
]
