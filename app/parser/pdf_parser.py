"""PDF parsing using PyMuPDF (fitz) for text/fonts/images + pdfplumber for tables.

Scanned (image-only) PDFs are detected and routed to PaddleOCR when available.
"""

import re
from pathlib import Path

try:
    import fitz
except Exception:
    fitz = None

try:
    import pdfplumber
except Exception:
    pdfplumber = None

from app.parser import ocr
from app.schemas.document import (
    FontRun,
    ImageInfo,
    Margins,
    Paragraph,
    ParsedDocument,
    Section,
    Table,
)

_PAGE_NUMBER_RE = re.compile(r"^\s*\d+\s*$")
_SCANNED_PAGE_MIN_CHARS = 50


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def _is_bold(flags: int) -> bool:
    return bool(flags & 2**4)


def _is_italic(flags: int) -> bool:
    return bool(flags & 2**1)


def parse_pdf(path: str | Path) -> ParsedDocument:
    path = Path(path)
    if fitz is None:
        raise RuntimeError("PyMuPDF (fitz) is unavailable in this serverless environment.")
    pdf = fitz.open(str(path))


    paragraphs: list[Paragraph] = []
    text_by_page: list[str] = []
    sections: list[Section] = []
    images: list[ImageInfo] = []
    page_numbers_found = 0
    header_chunks: list[str] = []
    footer_chunks: list[str] = []
    all_sizes: list[float] = []

    current_section: Section | None = None
    image_index = 0

    for page_no, page in enumerate(pdf):
        page_text = page.get_text()
        text_by_page.append(page_text)

        # --- images ---
        for info in page.get_image_info():
            image_index += 1
            images.append(
                ImageInfo(
                    index=image_index,
                    page=page_no + 1,
                    width_pt=info.get("width"),
                    height_pt=info.get("height"),
                )
            )

        if len(page_text.strip()) < _SCANNED_PAGE_MIN_CHARS:
            continue  # scanned page; OCR handled below

        # --- headers / footers / page numbers via bands ---
        page_rect = page.rect
        band_h = page_rect.height * 0.08
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                bbox = line["bbox"]
                text = "".join(span["text"] for span in line["spans"]).strip()
                if not text:
                    continue
                if bbox[1] < band_h:
                    header_chunks.append(text)
                elif bbox[3] > page_rect.height - band_h:
                    footer_chunks.append(text)
                    if _PAGE_NUMBER_RE.match(text):
                        page_numbers_found += 1

        # --- spans -> paragraphs, dominant font per line ---
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                spans = line["spans"]
                if not spans:
                    continue
                text = "".join(s["text"] for s in spans).strip()
                if not text:
                    continue
                sizes = [s["size"] for s in spans]
                all_sizes.extend(sizes)
                fams = [s["font"] for s in spans]
                dominant = FontRun(
                    family=fams[0],
                    size_pt=round(max(sizes), 1),
                    bold=any(_is_bold(s["flags"]) for s in spans),
                    italic=any(_is_italic(s["flags"]) for s in spans),
                )
                para = Paragraph(
                    text=text,
                    style=None,
                    alignment=None,
                    line_spacing=None,
                    bullet=False,
                    runs=[dominant],
                    dominant_font=dominant,
                )
                paragraphs.append(para)
                if para.text.strip() == "":
                    continue
                # Heading heuristic: font size well above the running median.
                body_median = _median(all_sizes) or 11.0
                if dominant.size_pt and dominant.size_pt >= body_median * 1.4:
                    current_section = Section(
                        heading=para.text, heading_level=1, text=para.text
                    )
                    sections.append(current_section)
                elif current_section is not None:
                    current_section.text = (current_section.text + "\n" + para.text).strip()
                    current_section.paragraphs.append(para)
                else:
                    sections.append(
                        Section(heading="", heading_level=0, text=para.text, paragraphs=[para])
                    )

    # --- tables via pdfplumber ---
    tables: list[Table] = []
    try:
        import pdfplumber  # noqa: PLC0415

        with pdfplumber.open(str(path)) as pdfp:
            for p in pdfp.pages:
                for tbl in p.extract_tables() or []:
                    rows = [[(cell or "").strip() for cell in row] for row in tbl]
                    if rows:
                        tables.append(Table(rows=rows, style=None, has_header=len(rows) > 1))
    except Exception:
        pass

    # --- margins (average across pages, in inches) ---
    margins_acc = {"top": [], "bottom": [], "left": [], "right": []}
    for page in pdf:
        rect = page.rect
        blocks = page.get_text("blocks")
        if not blocks:
            continue
        min_x = min(b[0] for b in blocks)
        max_x = max(b[2] for b in blocks)
        min_y = min(b[1] for b in blocks)
        max_y = max(b[3] for b in blocks)
        if rect.width > 0 and rect.height > 0:
            margins_acc["left"].append(min_x / 72.0)
            margins_acc["right"].append((rect.width - max_x) / 72.0)
            margins_acc["top"].append(min_y / 72.0)
            margins_acc["bottom"].append((rect.height - max_y) / 72.0)

    margins = Margins(
        top_in=round(_median(margins_acc["top"]), 2) if margins_acc["top"] else None,
        bottom_in=round(_median(margins_acc["bottom"]), 2) if margins_acc["bottom"] else None,
        left_in=round(_median(margins_acc["left"]), 2) if margins_acc["left"] else None,
        right_in=round(_median(margins_acc["right"]), 2) if margins_acc["right"] else None,
    )

    # --- scanned page detection & OCR ---
    scanned_pages = [i for i, t in enumerate(text_by_page) if len(t.strip()) < _SCANNED_PAGE_MIN_CHARS]
    ocr_used = False
    if scanned_pages:
        ocr_texts = ocr.ocr_pdf(path) if ocr.is_ocr_available() else []
        if ocr_texts:
            ocr_used = True
            for i in scanned_pages:
                if i < len(ocr_texts) and ocr_texts[i]:
                    text_by_page[i] = ocr_texts[i]
                    for line in ocr_texts[i].splitlines():
                        if line.strip():
                            paragraphs.append(
                                Paragraph(text=line.strip(), runs=[], dominant_font=None)
                            )

    pdf.close()
    return ParsedDocument(
        filename=path.name,
        file_type="pdf",
        parser="pdf+ocr" if ocr_used else "pdf",
        ocr_used=ocr_used,
        page_count=len(text_by_page),
        margins=margins,
        sections=sections,
        tables=tables,
        images=images,
        header_text=" | ".join(dict.fromkeys(header_chunks)),
        footer_text=" | ".join(dict.fromkeys(footer_chunks)),
        page_numbers_present=page_numbers_found >= max(1, len(text_by_page) - 1),
        paragraphs=paragraphs,
        text_by_page=text_by_page,
    )