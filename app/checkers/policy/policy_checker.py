"""Module 7: Policy Compliance Checker (rule-based, no LLM).

Config-driven checklist (config/policy_checklist.yaml): minimum pages, minimum
images, required signature, and attached-document keywords (feedback form,
attendance sheet, budget, invitation, brochure).
"""

from typing import Optional

from app.config_loader import load_policy_checklist
from app.schemas.document import ParsedDocument
from app.schemas.modules import PolicyItemResult, PolicyResult


class PolicyChecker:
    def __init__(self, config: Optional[dict] = None):
        self.config = config or load_policy_checklist()

    def _all_text(self, doc: ParsedDocument) -> str:
        parts = [doc.raw_text, doc.header_text, doc.footer_text]
        for table in doc.tables:
            for row in table.rows:
                parts.extend(row)
        return "\n".join(parts)

    def _check_item(self, item: dict, doc: ParsedDocument) -> PolicyItemResult:
        rule = item["rule"]
        text = self._all_text(doc)

        if rule == "min_pages":
            target = item["value"]
            ok = doc.page_count >= target
            return PolicyItemResult(
                id=item["id"], label=item["label"], passed=ok,
                detail=f"{doc.page_count} page(s), need >= {target}",
            )

        if rule == "min_images":
            target = item["value"]
            ok = len(doc.images) >= target
            return PolicyItemResult(
                id=item["id"], label=item["label"], passed=ok,
                detail=f"{len(doc.images)} image(s), need >= {target}",
            )

        if rule == "keyword":
            keywords = [k.lower() for k in item.get("keywords", [])]
            lowered = text.lower()
            found = [k for k in keywords if k in lowered]
            ok = bool(found)
            return PolicyItemResult(
                id=item["id"], label=item["label"], passed=ok,
                detail=f"found: {', '.join(found) or 'none'}"
                if ok else "keyword(s) not found: " + ", ".join(keywords),
            )

        return PolicyItemResult(
            id=item["id"], label=item["label"], passed=False,
            detail=f"unknown rule type '{rule}'",
        )

    def check(self, doc: ParsedDocument) -> PolicyResult:
        items = [self._check_item(item, doc) for item in self.config["items"]]
        return PolicyResult(items=items)