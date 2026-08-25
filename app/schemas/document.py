"""Normalized document object produced by the Parser (module 1) and consumed
by every downstream module. One schema set for DOCX and PDF output."""

from typing import Optional

from pydantic import BaseModel, Field


class FontRun(BaseModel):
    family: Optional[str] = None
    size_pt: Optional[float] = None
    bold: bool = False
    italic: bool = False


class Paragraph(BaseModel):
    text: str = ""
    style: Optional[str] = None
    alignment: Optional[str] = None  # left | center | right | justify
    line_spacing: Optional[float] = None
    bullet: bool = False
    list_marker: Optional[str] = None  # "•", "-", "*", ... when bulleted
    runs: list[FontRun] = Field(default_factory=list)
    dominant_font: Optional[FontRun] = None


class Section(BaseModel):
    heading: str = ""
    heading_level: int = 0
    text: str = ""
    paragraphs: list[Paragraph] = Field(default_factory=list)


class TableCell(BaseModel):
    text: str = ""


class Table(BaseModel):
    caption: str = ""
    rows: list[list[str]] = Field(default_factory=list)
    style: Optional[str] = None
    has_header: bool = False


class ImageInfo(BaseModel):
    index: int
    page: int = 0
    width_pt: Optional[float] = None
    height_pt: Optional[float] = None
    alignment: Optional[str] = None
    caption: Optional[str] = None


class Margins(BaseModel):
    top_in: Optional[float] = None
    bottom_in: Optional[float] = None
    left_in: Optional[float] = None
    right_in: Optional[float] = None


class ParsedDocument(BaseModel):
    filename: str
    file_type: str  # docx | pdf
    parser: str = ""  # docx | pdf | pdf+ocr
    ocr_used: bool = False
    page_count: int = 0
    margins: Margins = Field(default_factory=Margins)
    sections: list[Section] = Field(default_factory=list)
    tables: list[Table] = Field(default_factory=list)
    images: list[ImageInfo] = Field(default_factory=list)
    header_text: str = ""
    footer_text: str = ""
    page_numbers_present: bool = False
    paragraphs: list[Paragraph] = Field(default_factory=list)
    text_by_page: list[str] = Field(default_factory=list)

    @property
    def raw_text(self) -> str:
        return "\n".join(p.text for p in self.paragraphs if p.text)

    @property
    def text_with_metadata(self) -> str:
        """Text plus extracted metadata - useful for LLM prompts."""
        parts = [
            f"Filename: {self.filename}",
            f"Pages: {self.page_count}",
            f"Tables: {len(self.tables)}",
            f"Images: {len(self.images)}",
        ]
        parts.append("---- HEADER ----")
        parts.append(self.header_text or "(none)")
        parts.append("---- BODY ----")
        parts.append(self.raw_text)
        parts.append("---- FOOTER ----")
        parts.append(self.footer_text or "(none)")
        return "\n".join(parts)