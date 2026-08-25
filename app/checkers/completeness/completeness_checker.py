"""Module 4: Content Completeness Checker (LLM + deterministic fallback)."""

import logging
import re
from typing import Optional

from app.config import get_settings
from app.llm.client import LLMUnavailableError, get_llm_client
from app.llm.prompts import completeness_prompt
from app.schemas.document import ParsedDocument
from app.schemas.modules import CompletenessItem, CompletenessResult

log = logging.getLogger(__name__)

# Items to check: (key, label, fallback_keywords)
_COMPLETENESS_ITEMS = [
    ("event_objective", "Event Objective", ["objective", "aim", "purpose", "goal"]),
    ("speaker_introduction", "Speaker Introduction", ["speaker", "resource person", "presenter", "bio", "biography"]),
    ("lecture_summary", "Lecture Summary", ["summary", "synopsis", "overview", "lecture covered"]),
    ("learning_outcomes", "Learning Outcomes", ["learning outcome", "outcome", "outcomes"]),
    ("student_participation", "Student Participation", ["participation", "attendance", "students attended", "questions", "interaction"]),
    ("conclusion", "Conclusion", ["conclusion", "closing", "wrap up", "closing remarks"]),
]

_FALLBACK_MIN_CHARS = 120  # min text length around a match to count as "adequate"


class CompletenessChecker:
    def __init__(self, settings=None, llm_client=None):
        self.settings = settings or get_settings()
        self.llm = llm_client or get_llm_client()

    def _deterministic_check(self, doc: ParsedDocument) -> CompletenessResult:
        """Keyword-based fallback when LLM is unavailable."""
        text = (doc.raw_text + "\n" + doc.header_text + "\n" + doc.footer_text).lower()
        items = []
        present = []
        missing = []
        notes = {}

        for key, label, keywords in _COMPLETENESS_ITEMS:
            found = any(kw in text for kw in keywords)
            evidence = ""
            if found:
                # find a snippet for the note
                for kw in keywords:
                    m = re.search(re.escape(kw), doc.raw_text, re.IGNORECASE)
                    if m:
                        start = max(0, m.start() - 60)
                        evidence = doc.raw_text[start : m.end() + 60].replace("\n", " ")
                        break
            adequate = found and len(evidence) >= _FALLBACK_MIN_CHARS
            items.append(CompletenessItem(
                name=key, present=found, adequate=adequate,
                note=evidence[:160] if evidence else "keyword not found",
            ))
            if found:
                present.append(key)
            else:
                missing.append(key)
            notes[key] = evidence[:200] if evidence else "not detected"

        return CompletenessResult(present=present, missing=missing, notes=notes, items=items)

    def _parse_llm_result(self, data: dict) -> CompletenessResult:
        present = [k for k in data.get("present", []) if isinstance(k, str)]
        missing = [k for k in data.get("missing", []) if isinstance(k, str)]
        notes = {k: str(v) for k, v in data.get("notes", {}).items() if isinstance(k, str)}

        # Validate against known keys
        known = {k for k, _, _ in _COMPLETENESS_ITEMS}
        present = [p for p in present if p in known]
        missing = [m for m in missing if m in known]

        items = []
        for key, label, _ in _COMPLETENESS_ITEMS:
            items.append(CompletenessItem(
                name=key,
                present=key in present,
                adequate=key in present,  # LLM returns present only when adequate
                note=notes.get(key, ""),
            ))
        return CompletenessResult(present=present, missing=missing, notes=notes, items=items)

    async def check(self, doc: ParsedDocument) -> CompletenessResult:
        text = doc.text_with_metadata
        if not text.strip():
            return self._deterministic_check(doc)

        if not self.settings.enable_llm or not self.llm.available:
            log.info("LLM disabled; using deterministic completeness fallback")
            return self._deterministic_check(doc)

        try:
            system, user = completeness_prompt(text)
            data = await self.llm.structured(system, user)
            return self._parse_llm_result(data)
        except (LLMUnavailableError, ValueError, Exception) as exc:
            log.warning("LLM completeness check failed (%s); falling back", exc)
            return self._deterministic_check(doc)