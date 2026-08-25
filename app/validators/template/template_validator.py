"""Module 2: Template Validator (rule-based, no LLM).

Checks presence of required fields against a declarative YAML checklist
(config/required_fields.yaml). Fields are detected with regex/keyword heuristics
over the extracted text, images, and tables of the parsed document.
"""

import re
from typing import Optional

from app.config_loader import load_required_fields
from app.schemas.document import ParsedDocument
from app.schemas.modules import FieldCheck, TemplateCheckResult


class TemplateValidator:
    def __init__(self, config: Optional[dict] = None):
        self.config = config or load_required_fields()

    def _all_text(self, doc: ParsedDocument) -> str:
        parts = [doc.raw_text, doc.header_text, doc.footer_text]
        for table in doc.tables:
            for row in table.rows:
                parts.extend(row)
        return "\n".join(parts)

    def _check_field(self, field: dict, doc: ParsedDocument) -> FieldCheck:
        fid = field["id"]
        source = field.get("source", "text")

        if source == "images":
            if fid == "university_logo":
                passed = any(img.page == 1 for img in doc.images)
                return FieldCheck(
                    id=fid, label=field["label"], passed=passed,
                    evidence=f"{len(doc.images)} image(s) total" if not passed
                    else f"image on page 1 (index {next(i.index for i in doc.images if i.page == 1)})",
                )
            if fid == "photos":
                passed = len(doc.images) >= 2
                return FieldCheck(
                    id=fid, label=field["label"], passed=passed,
                    evidence=f"{len(doc.images)} image(s) found (need >= 2)",
                )
            passed = len(doc.images) > 0
            return FieldCheck(
                id=fid, label=field["label"], passed=passed,
                evidence=f"{len(doc.images)} image(s) found",
            )

        if source == "tables":
            table_text = " ".join(
                cell for table in doc.tables for row in table.rows for cell in row
            )
            passed, evidence = self._match_patterns(field.get("patterns", []), table_text)
            return FieldCheck(id=fid, label=field["label"], passed=passed, evidence=evidence)

        text = self._all_text(doc)
        passed, evidence = self._match_patterns(field.get("patterns", []), text)
        return FieldCheck(id=fid, label=field["label"], passed=passed, evidence=evidence)

    @staticmethod
    def _match_patterns(patterns: list[str], text: str) -> tuple[bool, str]:
        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                start = max(0, m.start() - 30)
                snippet = text[start : m.end() + 30].replace("\n", " ")
                return True, f'match "{m.group(0)[:60]}" in: ...{snippet}...'
        return False, "no match found"

    def validate(self, doc: ParsedDocument) -> TemplateCheckResult:
        checks = [self._check_field(f, doc) for f in self.config["fields"]]
        missing = [c.label for c in checks if not c.passed]
        return TemplateCheckResult(checks=checks, missing=missing)