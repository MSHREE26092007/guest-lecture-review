"""OCR fallback for scanned/image-based PDFs via PaddleOCR.

PaddleOCR + PaddlePaddle are heavy and optional. This module imports them lazily
so the rest of the system works without them. If OCR is unavailable, the parser
reports the PDF as scanned but returns empty text for the affected pages.
"""

from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger(__name__)

_ocr = None
_ocr_available: bool | None = None


def is_ocr_available() -> bool:
    global _ocr, _ocr_available
    if _ocr_available is not None:
        return _ocr_available
    try:
        from paddleocr import PaddleOCR  # type: ignore

        _ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        _ocr_available = True
    except Exception as exc:  # pragma: no cover - depends on optional deps
        log.warning("PaddleOCR unavailable (%s). Scanned PDFs will not be OCR'd.", exc)
        _ocr_available = False
    return _ocr_available


def ocr_pdf(path: str | Path) -> list[str]:
    """OCR every page of a PDF, returning one text string per page.

    Returns a list of empty strings (length = page count) if OCR is unavailable.
    """
    if not is_ocr_available():
        return []
    import fitz  # noqa: PLC0415

    texts: list[str] = []
    with fitz.open(str(path)) as pdf:
        for page in pdf:
            pix = page.get_pixmap(dpi=200)
            image_bytes = pix.tobytes("png")
            result = _ocr.ocr(image_bytes, cls=True)  # type: ignore
            page_text = ""
            if result and result[0]:
                for line in result[0]:
                    for item in line:
                        page_text += str(item[1][0]) + " "
            texts.append(page_text.strip())
    return texts