"""Shared fixtures: generate sample DOCX files once per session and parse them."""

from pathlib import Path

import pytest

from app.parser import parse_document
from scripts.generate_samples import generate_bad_report, generate_good_report

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def good_docx() -> Path:
    path = FIXTURES_DIR / "report_good.docx"
    if not path.exists():
        generate_good_report(path)
    return path


@pytest.fixture(scope="session")
def bad_docx() -> Path:
    path = FIXTURES_DIR / "report_bad.docx"
    if not path.exists():
        generate_bad_report(path)
    return path


@pytest.fixture(scope="session")
def good_doc(good_docx):
    return parse_document(good_docx)


@pytest.fixture(scope="session")
def bad_doc(bad_docx):
    return parse_document(bad_docx)