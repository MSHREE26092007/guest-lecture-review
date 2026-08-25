"""Module 1: Document Parser. Dispatches to the DOCX or PDF parser."""

from pathlib import Path

from app.parser.docx_parser import parse_docx
from app.parser.pdf_parser import parse_pdf
from app.schemas.document import ParsedDocument

SUPPORTED_EXTENSIONS = {".docx", ".pdf"}


def parse_document(path: str | Path) -> ParsedDocument:
    path = Path(path)
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}"
        )
    if ext == ".docx":
        return parse_docx(path)
    return parse_pdf(path)