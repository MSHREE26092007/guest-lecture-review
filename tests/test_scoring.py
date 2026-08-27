"""Unit tests for the Scoring Agent (Module 8)."""

import pytest

from app.checkers.completeness.completeness_checker import CompletenessChecker
from app.checkers.grammar.grammar_checker import GrammarChecker
from app.checkers.policy.policy_checker import PolicyChecker
from app.checkers.semantic.semantic_checker import SemanticChecker
from app.scoring.scoring_agent import compute_report
from app.validators.formatting.formatting_validator import FormattingValidator
from app.validators.template.template_validator import TemplateValidator


@pytest.mark.anyio
async def test_good_report_scoring(good_doc):
    t_res = TemplateValidator().validate(good_doc)
    f_res = FormattingValidator().validate(good_doc)
    c_res = await CompletenessChecker().check(good_doc)
    s_res = await SemanticChecker().check(good_doc)
    g_res = await GrammarChecker().check(good_doc)
    p_res = PolicyChecker().check(good_doc)

    report = compute_report(t_res, f_res, c_res, s_res, g_res, p_res, good_doc)

    assert report.overall_max == 100.0
    assert report.overall_score >= 70.0
    assert report.grade in {"A", "B"}
    assert len(report.criteria) == 8
    assert len(report.suggestions) <= 5


@pytest.mark.anyio
async def test_bad_report_scoring(bad_doc):
    t_res = TemplateValidator().validate(bad_doc)
    f_res = FormattingValidator().validate(bad_doc)
    c_res = await CompletenessChecker().check(bad_doc)
    s_res = await SemanticChecker().check(bad_doc)
    g_res = await GrammarChecker().check(bad_doc)
    p_res = PolicyChecker().check(bad_doc)

    report = compute_report(t_res, f_res, c_res, s_res, g_res, p_res, bad_doc)

    assert report.overall_max == 100.0
    assert report.overall_score < 70.0
    assert report.grade in {"C", "D", "F"}
    assert len(report.missing_items) > 0
    assert len(report.formatting_errors) > 0
