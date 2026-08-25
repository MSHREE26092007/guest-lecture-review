"""Pydantic input/output schemas for every pipeline module (2-8)."""

from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------- module 2
class FieldCheck(BaseModel):
    id: str
    label: str
    passed: bool
    evidence: str = ""


class TemplateCheckResult(BaseModel):
    checks: list[FieldCheck] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def total(self) -> int:
        return len(self.checks)


# ---------------------------------------------------------------- module 3
class FormattingRuleResult(BaseModel):
    rule: str
    label: str
    passed: bool
    expected: Any = None
    actual: Any = None
    severity: str = "major"  # minor | major


class FormattingCheckResult(BaseModel):
    results: list[FormattingRuleResult] = Field(default_factory=list)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def errors(self) -> list[FormattingRuleResult]:
        return [r for r in self.results if not r.passed]


# ---------------------------------------------------------------- module 4
class CompletenessItem(BaseModel):
    name: str
    present: bool
    adequate: bool = False
    note: str = ""


class CompletenessResult(BaseModel):
    present: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    notes: dict[str, str] = Field(default_factory=dict)
    items: list[CompletenessItem] = Field(default_factory=list)

    @property
    def passed_count(self) -> int:
        return sum(1 for i in self.items if i.present and i.adequate)

    @property
    def total(self) -> int:
        return len(self.items)


# ---------------------------------------------------------------- module 5
class SemanticPair(BaseModel):
    a: str
    b: str
    similarity: float = 0.0
    threshold: float = 0.35
    flagged: bool = False


class SemanticResult(BaseModel):
    quality: dict[str, Any] = Field(default_factory=dict)  # LLM subjective pass
    mismatches: list[SemanticPair] = Field(default_factory=list)
    llm_notes: str = ""
    embeddings_enabled: bool = False

    @property
    def passed_count(self) -> int:
        score = 0
        n = 0
        if "meaningful" in self.quality:
            n += 1
            score += 1 if self.quality["meaningful"] else 0
        if "aligned_with_title" in self.quality:
            n += 1
            score += 1 if self.quality["aligned_with_title"] else 0
        if not self.mismatches:
            n += 1
            score += 1
        return score if n else 0

    @property
    def total(self) -> int:
        n = 0
        if "meaningful" in self.quality:
            n += 1
        if "aligned_with_title" in self.quality:
            n += 1
        n += 1  # embedding mismatch check
        return n


# ---------------------------------------------------------------- module 6
class GrammarIssue(BaseModel):
    location: str = ""
    severity: str = "info"  # info | warning | error
    message: str = ""
    suggestion: str = ""


class GrammarResult(BaseModel):
    issues: list[GrammarIssue] = Field(default_factory=list)
    llm_tone_notes: str = ""
    checker: str = "languagetool"  # languagetool | llm | none

    @property
    def passed_count(self) -> int:
        """Issues weighted by severity - a clean doc counts as 1."""
        return max(0, 1 - len(self.issues) / max(len(self.issues) + 1, 1))

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity in ("warning", "error"))


# ---------------------------------------------------------------- module 7
class PolicyItemResult(BaseModel):
    id: str
    label: str
    passed: bool
    detail: str = ""


class PolicyResult(BaseModel):
    items: list[PolicyItemResult] = Field(default_factory=list)

    @property
    def passed_count(self) -> int:
        return sum(1 for i in self.items if i.passed)

    @property
    def total(self) -> int:
        return len(self.items)


# ---------------------------------------------------------------- module 8
class CriterionScore(BaseModel):
    id: str
    label: str
    weight: float
    score: float = 0.0
    max_score: float = 0.0
    mode: str = ""
    detail: str = ""


class ImprovementSuggestion(BaseModel):
    title: str
    detail: str = ""


class FinalReport(BaseModel):
    submission_id: str = ""
    filename: str = ""
    overall_score: float = 0.0
    overall_max: float = 100.0
    grade: str = ""
    criteria: list[CriterionScore] = Field(default_factory=list)
    missing_items: list[str] = Field(default_factory=list)
    formatting_errors: list[FormattingRuleResult] = Field(default_factory=list)
    suggestions: list[ImprovementSuggestion] = Field(default_factory=list)
    module_summary: dict[str, Any] = Field(default_factory=dict)
    raw: dict[str, Any] = Field(default_factory=dict)  # full module results, JSON-serializable


# ---------------------------------------------------------------- misc
class ModuleError(BaseModel):
    module: str
    message: str


class ModuleResult(BaseModel):
    module: str
    status: str = "pending"  # pending | running | done | failed
    error: Optional[str] = None
    output: Optional[Any] = None