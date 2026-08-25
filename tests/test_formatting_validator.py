"""Unit tests for module 3: Formatting Validator (rule-based)."""

from app.schemas.document import ParsedDocument
from app.validators.formatting.formatting_validator import FormattingValidator


def _failed_rules(doc: ParsedDocument) -> list[str]:
    return [r.rule for r in FormattingValidator().validate(doc).results if not r.passed]


def test_good_report_passes_all_formatting_rules(good_doc: ParsedDocument):
    assert _failed_rules(good_doc) == []


def test_bad_report_fails_expected_rules(bad_doc: ParsedDocument):
    failed = set(_failed_rules(bad_doc))
    expected = {
        "body_font_family",   # Times New Roman != Calibri
        "body_font_size",     # 12 != 11
        "line_spacing",       # 2.0 != 1.15
        "margin_top",
        "margin_bottom",
        "margin_left",
        "margin_right",       # 0.5" != 1.0"
        "page_numbers",       # no PAGE field
        "headings_style",     # zero heading-styled paragraphs
        "image_alignment",    # left != center
    }
    assert expected <= failed, f"missing failures: {expected - failed}"


def test_good_report_uses_expected_values(good_doc: ParsedDocument):
    result = FormattingValidator().validate(good_doc)
    by_rule = {r.rule: r for r in result.results}
    assert by_rule["body_font_family"].actual.lower() == "calibri"
    assert by_rule["body_font_size"].actual == 11
    assert by_rule["line_spacing"].actual == 1.15
    assert by_rule["margin_left"].actual == 1.0
    assert by_rule["page_numbers"].actual is True
    assert set(by_rule["image_alignment"].actual) == {"center"}