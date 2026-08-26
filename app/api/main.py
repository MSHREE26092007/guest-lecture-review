"""FastAPI entry point for the Guest Lecture Document Review Agent."""

import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from app.api.ui_page import HTML_PAGE

from app.orchestration.graph import build_graph
from app.orchestration.state import PipelineState, ModuleStatus
from app.parser import parse_document
from app.schemas.modules import FinalReport

app = FastAPI(title="Guest Lecture Document Review Agent")

@app.get("/", response_class=HTMLResponse)
def root():
    return HTMLResponse(content=HTML_PAGE)

@app.get("/health")
def health():
    return {"healthy": True}

# Simple in-memory store for pipeline states (keyed by submission id)
# In production, use Redis or a database.
submissions: dict[str, PipelineState] = {}

Graph = build_graph()


class UploadResponse(BaseModel):
    submission_id: str
    filename: str


@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Accept a DOCX or PDF upload and store it."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {".docx", ".pdf"}:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    submission_id = str(uuid.uuid4())
    upload_dir = Path(__file__).resolve().parent.parent / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / f"{submission_id}{ext}"

    # Save uploaded file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    submissions[submission_id] = PipelineState(
        submission_id=submission_id,
        filename=str(file_path),
        status=ModuleStatus.pending,
    )

    return UploadResponse(submission_id=submission_id, filename=file.filename)


@app.post("/review/{submission_id}")
def review(submission_id: str):
    """Run the full review pipeline for a submitted document."""
    state = submissions.get(submission_id)
    if not state:
        raise HTTPException(status_code=404, detail="Submission not found")

    # If already done, return existing result
    if state.final_report is not None:
        return JSONResponse(content=state.final_report.model_dump() if state.final_report else {})

    # Run the graph to completion
    try:
        result_dict = asyncio.run(Graph.ainvoke(state))
        final_state = PipelineState(**result_dict)
        submissions[state.submission_id] = final_state
        return JSONResponse(content=final_state.final_report.model_dump() if final_state.final_report else {})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {exc}")


@app.get("/status/{submission_id}")
def status(submission_id: str):
    """Return the current pipeline status for a submission."""
    state = submissions.get(submission_id)
    if not state:
        raise HTTPException(status_code=404, detail="Submission not found")
    return {
        "submission_id": state.submission_id,
        "status": state.status,
        "filename": state.filename,
        "template_status": state.template_status,
        "formatting_status": state.formatting_status,
        "completeness_status": state.completeness_status,
        "semantic_status": state.semantic_status,
        "grammar_status": state.grammar_status,
        "policy_status": state.policy_status,
        "error": state.error,
        "final_report": state.final_report.model_dump() if state.final_report else None,
    }


class ReportResponse(BaseModel):
    overall_score: float
    overall_max: float
    grade: str
    criteria: list[dict[str, Any]]
    missing_items: list[str]
    formatting_errors: list[dict[str, Any]]
    suggestions: list[dict[str, Any]]


@app.get("/report/{submission_id}", response_model=ReportResponse)
def report(submission_id: str):
    """Return the final scored report for a submission."""
    state = submissions.get(submission_id)
    if not state:
        raise HTTPException(status_code=404, detail="Submission not found")
    if state.final_report is None:
        raise HTTPException(status_code=404, detail="Report not yet generated")

    r = state.final_report
    # Convert criterion objects to dicts for JSON serialization
    criteria_list = []
    for c in r.criteria:
        criteria_list.append(
            {
                "id": c.id,
                "label": c.label,
                "weight": c.weight,
                "score": c.score,
                "max_score": c.max_score,
                "mode": c.mode,
                "detail": c.detail,
            }
        )

    return ReportResponse(
        overall_score=r.overall_score,
        overall_max=r.overall_max,
        grade=r.grade,
        criteria=criteria_list,
        missing_items=r.missing_items,
        formatting_errors=[
            {"rule": e.rule, "label": e.label, "severity": e.severity, "expected": str(e.expected) if e.expected else None, "actual": str(e.actual) if e.actual else None}
            for e in r.formatting_errors
        ],
        suggestions=[{"title": s.title, "detail": s.detail} for s in r.suggestions],
    )