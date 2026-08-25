"""Module 5: Semantic Quality Checker (LLM + embeddings).

- LLM pass: quality judgments on the lecture summary (meaningful, non-repetitive,
  adequate length, aligned with title).
- Embeddings pass: cosine similarity between title, objectives, summary, and
  learning outcomes. Flags pairs below configurable threshold.
"""

import logging
import re
from typing import Optional

from app.checkers.semantic.embeddings import (
    cosine_similarity,
    embed_text,
    is_embeddings_available,
)
from app.config import get_settings
from app.llm.client import get_llm_client, LLMUnavailableError
from app.llm.prompts import semantic_quality_prompt
from app.schemas.document import ParsedDocument
from app.schemas.modules import SemanticPair, SemanticResult

log = logging.getLogger(__name__)


def _extract_sections(doc: ParsedDocument) -> dict[str, str]:
    """Find key sections by heading keywords. Returns dict of section_name -> text."""
    sections = {}
    for s in doc.sections:
        h = s.heading.lower()
        text = s.text.strip()
        if not text:
            continue
        if re.search(r"objective|aim|purpose", h):
            sections["objectives"] = text
        elif re.search(r"summary|synopsis|overview", h):
            sections["summary"] = text
        elif re.search(r"learning\s+outcome|outcomes?", h):
            sections["outcomes"] = text
        elif re.search(r"participation|attendance", h):
            sections["participation"] = text
        elif re.search(r"conclusion|closing|wrap", h):
            sections["conclusion"] = text
    # Title from first heading level 1 or filename
    for s in doc.sections:
        if s.heading_level == 1:
            sections["title"] = s.heading
            break
    if "title" not in sections:
        sections["title"] = doc.filename.replace(".docx", "").replace(".pdf", "")
    return sections


class SemanticChecker:
    def __init__(self, settings=None, llm_client=None):
        self.settings = settings or get_settings()
        self.llm = llm_client or get_llm_client()

    async def check(self, doc: ParsedDocument) -> SemanticResult:
        sections = _extract_sections(doc)
        title = sections.get("title", "")
        summary = sections.get("summary", "")

        quality = {}
        llm_notes = ""

        # --- LLM quality pass ---
        if self.settings.enable_llm and self.llm.available:
            try:
                system, user = semantic_quality_prompt(title, summary)
                data = await self.llm.structured(system, user)
                quality = {
                    "meaningful": bool(data.get("meaningful", False)),
                    "non_repetitive": bool(data.get("non_repetitive", False)),
                    "adequate_length": bool(data.get("adequate_length", False)),
                    "aligned_with_title": bool(data.get("aligned_with_title", False)),
                }
                llm_notes = str(data.get("notes", ""))
            except (LLMUnavailableError, ValueError, Exception) as exc:
                log.warning("LLM semantic quality pass failed: %s", exc)

        # --- Embeddings pass ---
        mismatches = []
        embeddings_enabled = False
        threshold = self.settings.semantic_threshold

        if self.settings.enable_embeddings and is_embeddings_available():
            embeddings_enabled = True
            pairs_to_check = [
                ("title", "objectives"),
                ("title", "summary"),
                ("objectives", "summary"),
                ("objectives", "outcomes"),
                ("summary", "outcomes"),
            ]
            vecs = {}
            for name in ("title", "objectives", "summary", "outcomes", "participation", "conclusion"):
                text = sections.get(name, "")
                if text:
                    vecs[name] = embed_text(text)

            for a_name, b_name in pairs_to_check:
                if a_name in vecs and b_name in vecs:
                    sim = cosine_similarity(vecs[a_name], vecs[b_name])
                    flagged = sim < threshold
                    mismatches.append(SemanticPair(
                        a=a_name, b=b_name,
                        similarity=round(sim, 3),
                        threshold=threshold,
                        flagged=flagged,
                    ))
                    if flagged:
                        log.info("Semantic mismatch: %s vs %s = %.3f (< %.2f)", a_name, b_name, sim, threshold)

        return SemanticResult(
            quality=quality,
            mismatches=mismatches,
            llm_notes=llm_notes,
            embeddings_enabled=embeddings_enabled,
        )