"""Text extraction from a document file, with OCR only when it is actually needed.

Born-digital text (.txt/.md/.json) is read straight through with no OCR
confidence. PDFs go through pypdf if it is installed. Images go through Tesseract
(via pytesseract) if both the package and the system binary are present. When an
image or PDF arrives but the optional `ocr` extra is not installed, this raises a
clear, actionable error rather than silently returning empty text - a blank
document would sail through the pipeline and produce a confidently wrong $0 return.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_TEXT_SUFFIXES = {".txt", ".md", ".text", ".json", ".csv"}
_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


class OcrUnavailableError(RuntimeError):
    """Raised when a scanned document needs OCR but the `ocr` extra is missing."""


def extract_text(path: Path) -> tuple[str, float | None]:
    """Return (text, ocr_confidence). Confidence is None for born-digital text."""
    suffix = path.suffix.lower()
    if suffix in _TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8", errors="replace"), None
    if suffix == ".pdf":
        return _read_pdf(path), None
    if suffix in _IMAGE_SUFFIXES:
        return _ocr_image(path)
    # Unknown suffix: try to read as text rather than guess a binary format.
    logger.warning("Unrecognised document suffix %s; reading as text", suffix)
    return path.read_text(encoding="utf-8", errors="replace"), None


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise OcrUnavailableError(
            f"{path.name} is a PDF; install the 'ocr' extra (pip install -e '.[ocr]') to read it"
        ) from exc
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _ocr_image(path: Path) -> tuple[str, float | None]:
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise OcrUnavailableError(
            f"{path.name} is an image; install the 'ocr' extra and the Tesseract binary to OCR it"
        ) from exc

    image = Image.open(path)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    text = pytesseract.image_to_string(image)
    # Mean word-level confidence, normalised to 0..1; -1 entries are non-text boxes.
    scores = [int(c) for c in data.get("conf", []) if str(c).lstrip("-").isdigit() and int(c) >= 0]
    confidence = (sum(scores) / len(scores) / 100.0) if scores else None
    return text, confidence
