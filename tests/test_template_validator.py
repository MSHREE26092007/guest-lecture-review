"""Unit tests for module 2: Template Validator (rule-based)."""

from app.schemas.document import ParsedDocument
from app.validators.template.template_validator import TemplateValidator


def test_good_report_passes_all_fields(good_doc: ParsedDocument):
    result = TemplateValidator().validate(good_doc)
    assert result.missing == [], f"unexpected missing fields: {result.missing}"
    assert result.passed_count == result.total


def test_bad_report_misses_expected_fields(bad_doc: ParsedDocument):
    result = TemplateValidator().validate(bad_doc)
    missing = set(result.missing)
    assert missing >= {
        "University Logo",
        "Department Name",
        "Designation",
        "Organization",
        "Date",
        "Time",
        "Venue",
        "Faculty Coordinator",
        "Learning Outcomes",
        "Schedule",
        "Student Attendance",
        "Photos",
        "Feedback",
        "Signature",
    }
    # The bad report still names the speaker and mentions a guest lecture.
    assert "Guest Lecture Title" not in missing
    assert "Speaker Name" not in missing


def test_config_driven_no_code_change(good_doc: ParsedDocument):
    """Fields come from YAML config, not code: simulate adding a field."""
    from app.config_loader import load_required_fields

    config = load_required_fields()
    config["fields"].append(
        {"id": "made_up_field", "label": "Made Up Field", "source": "text", "patterns": ["zzzz-not-in-doc"]}
    )
    result = TemplateValidator(config=config).validate(good_doc)
    assert "Made Up Field" in result.missing