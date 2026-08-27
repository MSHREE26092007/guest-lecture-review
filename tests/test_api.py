"""Unit tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Guest Lecture Document Review Agent" in response.text


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"healthy": True}


def test_upload_and_review_flow(good_docx):
    # 1. Upload
    with open(good_docx, "rb") as f:
        upload_resp = client.post("/upload", files={"file": ("report_good.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")})
    assert upload_resp.status_code == 200
    data = upload_resp.json()
    assert "submission_id" in data
    submission_id = data["submission_id"]

    # 2. Check status
    status_resp = client.get(f"/status/{submission_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["submission_id"] == submission_id

    # 3. Review
    review_resp = client.post(f"/review/{submission_id}")
    assert review_resp.status_code == 200
    report_data = review_resp.json()
    assert "overall_score" in report_data
    assert "grade" in report_data
    assert report_data["overall_max"] == 100.0

    # 4. Report endpoint
    final_resp = client.get(f"/report/{submission_id}")
    assert final_resp.status_code == 200
    assert final_resp.json()["grade"] == report_data["grade"]
