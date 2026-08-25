"""Unit tests for module 7: Policy Compliance Checker (rule-based)."""

from app.checkers.policy.policy_checker import PolicyChecker
from app.schemas.document import ParsedDocument


def _failed_items(doc: ParsedDocument) -> list[str]:
    return [i.id for i in PolicyChecker().check(doc).items if not i.passed]


def test_good_report_passes_all_policy_items(good_doc: ParsedDocument):
    assert _failed_items(good_doc) == []


def test_bad_report_fails_all_policy_items(bad_doc: ParsedDocument):
    failed = set(_failed_items(bad_doc))
    expected = {
        "min_pages",           # 1 page < 4
        "min_images",          # 1 image < 2
        "required_signature",  # no signature text
        "feedback_attached",   # no feedback keyword
        "attendance_attached", # no attendance keyword
        "budget_attached",     # no budget keyword
        "invitation_attached", # no invitation keyword
        "brochure_attached",   # no brochure keyword
    }
    assert expected <= failed, f"missing failures: {expected - failed}"


def test_good_report_pages_and_images(good_doc: ParsedDocument):
    result = PolicyChecker().check(good_doc)
    by_id = {i.id: i for i in result.items}
    assert by_id["min_pages"].detail.startswith(f"{good_doc.page_count} page")
    assert good_doc.page_count >= 4
    assert len(good_doc.images) >= 3