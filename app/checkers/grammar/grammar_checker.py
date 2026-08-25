"""Module 6: Grammar & Language Checker (LanguageTool + optional LLM tone)."""

import logging
from typing import Optional

import httpx

from app.config import get_settings
from app.llm.client import get_llm_client, LLMUnavailableError
from app.llm.prompts import grammar_tone_prompt
from app.schemas.document import ParsedDocument
from app.schemas.modules import GrammarIssue, GrammarResult

log = logging.getLogger(__name__)

# LanguageTool issue type → severity mapping
_LT_SEVERITY = {
    "misspelling": "error",
    "grammar": "warning",
    "style": "info",
    "whitespace": "info",
    "punctuation": "warning",
    "typo": "error",
    "locale-violation": "info",
    "capitalization": "warning",
    "non-conforming": "info",
}


class GrammarChecker:
    def __init__(self, settings=None, llm_client=None):
        self.settings = settings or get_settings()
        self.llm = llm_client or get_llm_client()

    async def _languagetool(self, text: str) -> list[GrammarIssue]:
        if not text.strip():
            return []
        payload = {"text": text, "language": "en-US", "enabledOnly": "false"}
        try:
            async with httpx.AsyncClient(timeout=self.settings.languagetool_timeout) as client:
                resp = await client.post(self.settings.languagetool_url, data=payload)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            log.warning("LanguageTool call failed: %s", exc)
            return []

        issues: list[GrammarIssue] = []
        for match in data.get("matches", []):
            rule = match.get("rule", {})
            issue_type = rule.get("issueType", "grammar")
            severity = _LT_SEVERITY.get(issue_type, "info")
            offset = match.get("offset", 0)
            length = match.get("length", 0)
            snippet = text[max(0, offset - 60) : offset + length + 60]
            loc = f"char {offset}: ...{snippet.replace(chr(10), ' ')}..."
            suggestion = ""
            if match.get("replacements"):
                suggestion = match["replacements"][0].get("value", "")
            issues.append(GrammarIssue(
                location=loc,
                severity=severity,
                message=match.get("message", ""),
                suggestion=suggestion,
            ))
        return issues

    async def _llm_tone(self, text: str) -> str:
        if not self.settings.enable_llm or not self.llm.available:
            return ""
        try:
            system, user = grammar_tone_prompt(text)
            data = await self.llm.structured(system, user)
            return f"Tone: {data.get('tone_assessment', 'unknown')}. {data.get('notes', '')}"
        except (LLMUnavailableError, ValueError, Exception) as exc:
            log.warning("LLM tone check failed: %s", exc)
            return ""

    async def check(self, doc: ParsedDocument) -> GrammarResult:
        text = doc.raw_text
        issues = await self._languagetool(text)
        tone_notes = await self._llm_tone(text)

        return GrammarResult(
            issues=issues,
            llm_tone_notes=tone_notes,
            checker="languagetool" if issues else "none",
        )