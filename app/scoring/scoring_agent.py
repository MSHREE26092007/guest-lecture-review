"""Module 8: Scoring Agent.

Rubric-driven aggregation of module results into per-criterion scores and a
final report with 3–5 improvement suggestions.

All criteria except overall_quality are computed deterministically from the
module outputs. The LLM is used only for the subjective overall_quality component.
"""

from typing import Any, Dict, List, Optional

from app.checkers.policy.policy_checker import PolicyResult
from app.checkers.completeness.completeness_checker import CompletenessResult
from app.checkers.semantic.semantic_checker import SemanticResult
from app.checkers.grammar.grammar_checker import GrammarResult
from app.validators.formatting.formatting_validator import FormattingCheckResult
from app.validators.template.template_validator import TemplateCheckResult
from app.schemas.document import ParsedDocument
from app.schemas.modules import (
    CriterionScore,
    FinalReport,
    ImprovementSuggestion,
    ModuleResult,
)

from app.config_loader import load_scoring_rubric

CRITERION_WEIGHTS_DEFAULT = {
    "template": 20,
    "formatting": 15,
    "completeness": 20,
    "grammar": 10,
    "learning_outcomes": 10,
    "images": 5,
    "signature": 5,
    "overall_quality": 15,
}


def _score_template(template_result: TemplateCheckResult, weight: float) -> float:
    n = template_result.total
    p = template_result.passed_count
    return round((p / n * weight) if n else 0.0, 2)


def _score_formatting(formatting_result: FormattingCheckResult, weight: float) -> float:
    n = formatting_result.total
    p = formatting_result.passed_count
    return round((p / n * weight) if n else 0.0, 2)


def _score_completeness(completeness_result: CompletenessResult, weight: float) -> float:
    n = len(completeness_result.items)
    p = completeness_result.passed_count
    return round((p / n * weight) if n else 0.0, 2)


def _score_grammar(grammar_result: GrammarResult, weight: float) -> float:
    # 10 points total; -1 per issue, floored at 0
    n = weight
    score = max(0.0, n - len(grammar_result.issues))
    return round(score, 2)


def _score_learning_outcomes(
    completeness_result: CompletenessResult,
    semantic_result: SemanticResult,
    weight: float,
) -> float:
    # 50% from completeness (learning_outcomes present & adequate),
    # 50% from embeddings similarity (non-flagged pairs).
    comp_pass = completeness_result.passed_count
    comp_total = max(1, len(completeness_result.items))

    # LLM quality judgments: passed_count / total (0-3)
    sem_pass = semantic_result.passed_count
    sem_total = max(1, semantic_result.total)

    comp_score = comp_pass / comp_total  # 0..1
    sem_score = sem_pass / sem_total  # 0..1

    combined = 0.5 * comp_score + 0.5 * sem_score
    return round(combined * weight, 2)


def _score_images(policy_result: PolicyResult, doc: ParsedDocument, weight: float, target: int = 3) -> float:
    # min(weight, image_count / target * weight)
    # Use doc.image count; proportional score based on target
    image_count = len(doc.images) if doc else 0
    if image_count == 0:
        return 0.0
    return round(min(weight, (image_count / target) * weight), 2)


def _score_signature(policy_result: PolicyResult, weight: float) -> float:
    sig_item = next((i for i in policy_result.items if i.id == "required_signature"), None)
    return weight if (sig_item and sig_item.passed) else 0.0


def _generate_suggestions(
    template_result: TemplateCheckResult,
    formatting_result: FormattingCheckResult,
    completeness_result: CompletenessResult,
    grammar_result: GrammarResult,
    policy_result: PolicyResult,
    doc: ParsedDocument,
) -> List[ImprovementSuggestion]:
    suggestions: List[ImprovementSuggestion] = []

    missing_labels = [c.label for c in template_result.checks if not c.passed]
    if missing_labels:
        items = ", ".join(missing_labels[:3])
        suggestions.append(
            ImprovementSuggestion(
                title="Add missing required fields",
                detail=f"Include the following required items: {items}.",
            )
        )

    errors = [r for r in formatting_result.results if not r.passed]
    if errors:
        rule_labels = [r.label for r in errors[:3]]
        suggestions.append(
            ImprovementSuggestion(
                title="Fix formatting issues",
                detail=f"Review the following formatting rules: {', '.join(rule_labels)}.",
            )
        )

    missing_content = [c.name for c in completeness_result.items if not c.present or not c.adequate]
    if missing_content:
        items = ", ".join(missing_content[:3])
        suggestions.append(
            ImprovementSuggestion(
                title="Expand content sections",
                detail=f"Develop the following sections: {items}.",
            )
        )

    if grammar_result.issues:
        n = len(grammar_result.issues)
        suggestions.append(
            ImprovementSuggestion(
                title="Run language polish",
                detail=f"Address {n} grammar/spelling issues for clearer academic tone.",
            )
        )

    if not policy_result.items or not any(i.passed for i in policy_result.items):
        missing_policy = [i.label for i in policy_result.items if not i.passed]
        items = ", ".join(missing_policy[:3])
        suggestions.append(
            ImprovementSuggestion(
                title="Attach supporting documents",
                detail=f"Ensure the following are attached: {items}.",
            )
        )

    # Default if nothing triggered
    if not suggestions:
        suggestions.append(
            ImprovementSuggestion(
                title="Review report completeness",
                detail="Check all required fields, formatting consistency, and grammar before final submission.",
            )
        )

    return suggestions[:5]  # cap at 5


def compute_report(
    template_result: TemplateCheckResult,
    formatting_result: FormattingCheckResult,
    completeness_result: CompletenessResult,
    semantic_result: SemanticResult,
    grammar_result: GrammarResult,
    policy_result: PolicyResult,
    doc: ParsedDocument,
    llm_overall_score: Optional[float] = None,
    llm_overall_max: float = 100.0,
) -> FinalReport:
    """Aggregate all module outputs into a FinalReport using the rubric."""

    rubric = load_scoring_rubric()
    weights = rubric["criteria"]  # list of dicts from yaml

    # Map criterion ids to weight and compute scores
    criteria_map = {c["id"]: c for c in weights}

    scores: List[CriterionScore] = []

    # Template
    t = _score_template(template_result, criteria_map["template"]["weight"])
    scores.append(
        CriterionScore(
            id="template",
            label="Template Compliance",
            weight=criteria_map["template"]["weight"],
            score=t,
            max_score=criteria_map["template"]["weight"],
            mode="ratio",
            detail=f"{template_result.passed_count}/{template_result.total} fields passed",
        )
    )

    # Formatting
    f = _score_formatting(formatting_result, criteria_map["formatting"]["weight"])
    scores.append(
        CriterionScore(
            id="formatting",
            label="Formatting",
            weight=criteria_map["formatting"]["weight"],
            score=f,
            max_score=criteria_map["formatting"]["weight"],
            mode="ratio",
            detail=f"{formatting_result.passed_count}/{formatting_result.total} rules passed",
        )
    )

    # Completeness
    c = _score_completeness(completeness_result, criteria_map["completeness"]["weight"])
    scores.append(
        CriterionScore(
            id="completeness",
            label="Content Completeness",
            weight=criteria_map["completeness"]["weight"],
            score=c,
            max_score=criteria_map["completeness"]["weight"],
            mode="ratio",
            detail=f"{completeness_result.passed_count}/{completeness_result.total} items adequate",
        )
    )

    # Grammar
    g = _score_grammar(grammar_result, criteria_map["grammar"]["weight"])
    scores.append(
        CriterionScore(
            id="grammar",
            label="Grammar & Language",
            weight=criteria_map["grammar"]["weight"],
            score=g,
            max_score=criteria_map["grammar"]["weight"],
            mode="grammar",
            detail=f"{len(grammar_result.issues)} issue(s) detected",
        )
    )

    # Learning Outcomes
    lo = _score_learning_outcomes(completeness_result, semantic_result, criteria_map["learning_outcomes"]["weight"])
    scores.append(
        CriterionScore(
            id="learning_outcomes",
            label="Learning Outcomes",
            weight=criteria_map["learning_outcomes"]["weight"],
            score=lo,
            max_score=criteria_map["learning_outcomes"]["weight"],
            mode="combined",
            detail="50% completeness + 50% semantic similarity",
        )
    )

    # Images
    i = _score_images(policy_result, doc, criteria_map["images"]["weight"], criteria_map["images"].get("target", 3))
    scores.append(
        CriterionScore(
            id="images",
            label="Images",
            weight=criteria_map["images"]["weight"],
            score=i,
            max_score=criteria_map["images"]["weight"],
            mode="images",
            detail=f"{len(doc.images) if doc else 0} image(s)",
        )
    )

    # Signature
    sig = _score_signature(policy_result, criteria_map["signature"]["weight"])
    scores.append(
        CriterionScore(
            id="signature",
            label="Signature",
            weight=criteria_map["signature"]["weight"],
            score=sig,
            max_score=criteria_map["signature"]["weight"],
            mode="binary",
            detail="present" if sig > 0 else "absent",
        )
    )

    # Overall Quality (subjective)
    if llm_overall_score is not None:
        overall = round(llm_overall_score / llm_overall_max * criteria_map["overall_quality"]["weight"], 2)
    else:
        # Fallback deterministic: average of other criterion scores / max possible * weight
        other_scores = [s.score for s in scores[:-1]]  # exclude overall_quality
        max_other = sum(s.max_score for s in scores[:-1])
        overall = round((sum(other_scores) / max_other * criteria_map["overall_quality"]["weight"]) if max_other else 0, 2)

    scores.append(
        CriterionScore(
            id="overall_quality",
            label="Overall Quality",
            weight=criteria_map["overall_quality"]["weight"],
            score=overall,
            max_score=criteria_map["overall_quality"]["weight"],
            mode="llm",
            detail="LLM subjective score" if llm_overall_score is not None else "deterministic fallback",
        )
    )

    total_score = round(sum(s.score for s in scores), 2)
    overall_max = sum(s.max_score for s in scores)

    grade = ""
    if total_score >= 85:
        grade = "A"
    elif total_score >= 70:
        grade = "B"
    elif total_score >= 50:
        grade = "C"
    elif total_score >= 40:
        grade = "D"
    else:
        grade = "F"

    missing_items = [c.label for c in template_result.checks if not c.passed]
    formatting_errors = [r for r in formatting_result.results if not r.passed]

    suggestions = _generate_suggestions(
        template_result, formatting_result, completeness_result, grammar_result, policy_result, doc
    )

    return FinalReport(
        submission_id=doc.filename if doc else "unknown",
        filename=doc.filename if doc else "unknown",
        overall_score=total_score,
        overall_max=overall_max,
        grade=grade,
        criteria=scores,
        missing_items=missing_items,
        formatting_errors=formatting_errors,
        suggestions=suggestions,
        raw={
            "template": template_result.model_dump(),
            "formatting": formatting_result.model_dump(),
            "completeness": completeness_result.model_dump(),
            "semantic": semantic_result.model_dump(),
            "grammar": grammar_result.model_dump(),
            "policy": policy_result.model_dump(),
        },
    )