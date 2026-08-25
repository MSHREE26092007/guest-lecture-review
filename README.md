# Guest Lecture Document Review Agent

## Overview

A full-stack system that ingests a guest lecture report (DOCX or PDF) and validates it against a university template, checking format, structure, content completeness, and quality, then outputs a score and review report.

The system follows a **7-module pipeline** coordinated by LangGraph, with a FastAPI back-end and Streamlit prototype UI.

---

## Architecture

### 7-Molecule Pipeline (Coordinator-Orchestrated)

| Module | Description | LLM |
|---|---|---|
| **1. Document Parser** | Extracts text, tables, images, fonts, headers/footers, page count, margins from DOCX (python-docx) and PDF (PyMuPDF + pdfplumber). Scanned PDFs routed to PaddleOCR (optional). | — |
| **2. Template Validator** | Rule-based checklist (YAML-driven) for required fields: University Logo, Department Name, Guest Lecture Title, Speaker Name, Designation, Organization, Date, Time, Venue, Faculty Coordinator, Learning Outcomes, Schedule, Student Attendance, Photos, Feedback, Signature. | No |
| **3. Formatting Validator** | Rule-based comparison of font family/size, heading size, bold/italics, line spacing, margins, page numbers, header/footer, table style, image alignment, bullet style against config-defined spec. | No |
| **4. Content Completeness Checker** | Sends extracted text to Claude API (claude-sonnet-4-6) with structured prompt; responds with JSON `{"present": [...], "missing": [...], "notes": {...}}`. JSON parsed with fence-stripping fallback. | Claude API |
| **5. Semantic Quality Checker** | LLM pass: meaningful/non-repetitive/sufficiently long summary aligned with title. Embeddings pass: sentence-transformers (all-mpnet-base-v2) cosine similarity between title, objectives, summary, learning outcomes; flags mismatches below configurable threshold (default 0.35). | Claude API + embeddings |
| **6. Grammar & Language Checker** | LanguageTool self-hosted/public API for grammar/spelling/passive-voice/sentence-completeness. Optional LLM supplement for academic-tone feedback. | LanguageTool + optional Claude |
| **7. Policy Compliance Checker** | Config-driven checklist: min pages, min images, required signatures, feedback form, attendance sheet, budget, invitation, brochure attached. | No |
| **8. Scoring Agent** | Rubric-driven aggregation (weights: Template 20, Formatting 15, Completeness 20, Grammar 10, Learning Outcomes 10, Images 5, Signature 5, Overall Quality 15 = 100). All criteria deterministic except Overall Quality (LLM subjective). | Claude API (subjective only) |

### Orchestration

- **LangGraph** StateGraph with checkpoint persistence (MemorySaver) so a failed module can be retried without re-running the whole pipeline.
- Node order: `Parser → [Template, Formatting] (parallel) → [Completeness, Semantic, Grammar] (parallel, LLM-heavy) → Policy → Scoring → Report`.
- Each node is a typed function with `PipelineState` input/output (Pydantic v2). Nodes skip if their result already marked `done`, enabling retry and persistent intermediate state.

### Tech Stack

- **Backend**: FastAPI (async), Pydantic v2 models for every module's I/O.
- **Frontend**: Streamlit prototype (file upload, live progress per module, final report view with pass/fail badges and score breakdown). React noted as v2 upgrade.
- **Document parsing**: python-docx, PyMuPDF, pdfplumber.
- **OCR**: PaddleOCR (optional, guarded import, scanned PDF fallback).
- **Embeddings**: sentence-transformers (all-mpnet-base-v2), optional; graceful degradation if not installed.
- **LLM**: Claude API (`api.anthropic.com/v1/messages`) via httpx; key read from env var `ANTHROPIC_API_KEY`; never hardcoded.
- **LanguageTool**: public API `https://api.languagetool.org/v2/check` by default; self-hosted URL configurable.
- **Database**: SQLAlchemy + Alembic for migrations; SQLite default for prototype, PostgreSQL via `DATABASE_URL` env var.
- **YAML configs**: all editable without code changes — `config/required_fields.yaml`, `config/formatting_spec.yaml`, `config/policy_checklist.yaml`, `config/scoring_rubric.yaml`.

---

## Directory Structure

```
guest-lecture-review/
├── README.md                    # this file
├── requirements.txt             # core dependencies
├── requirements-optional.txt    # heavy deps: paddleocr, paddlepaddle, sentence-transformers
├── .env.example                # template for environment variables
├── config/
│   ├── required_fields.yaml    # template required-field checklist
│   ├── formatting_spec.yaml    # formatting rule spec
│   ├── policy_checklist.yaml   # policy compliance checklist
│   └── scoring_rubric.yaml     # rubric weights and modes
├── app/
│   ├── __init__.py
│   ├── config.py               # pydantic settings (ANTHROPIC_API_KEY, DATABASE_URL, etc.)
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── document.py         # ParsedDocument model + per-module I/O models
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── docx_parser.py      # python-docx extraction + image alignment/caption
│   │   ├── pdf_parser.py       # PyMuPDF+pdfplumber + OCR guarded
│   │   └── ocr.py              # PaddleOCR lazy import
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── template/           template_validator.py
│   │   └── formatting/         formatting_validator.py
│   ├── checkers/
│   │   ├── __init__.py
│   │   ├── completeness/       completeness_checker.py
│   │   ├── semantic/           semantic_checker.py + embeddings.py
│   │   ├── grammar/            grammar_checker.py
│   │   └── policy/             policy_checker.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── client.py           # httpx Claude client + JSON parsing
│   │   └── prompts.py          # prompt templates for all LLM calls
│   ├── scoring/
│   │   └── scoring_agent.py    # rubric-driven score aggregation + report
│   ├── orchestration/
│   │   ├── __init__.py
│   │   ├── state.py            # PipelineState (Pydantic) + ModuleStatus enum
│   │   └── graph.py            # LangGraph StateGraph definition + build_graph()
│   ├── db/
│   │   ├── __init__.py
│   │   ├── models.py           # SQLAlchemy Submission model
│   │   └── session.py          # engine, SessionLocal, init_db()
│   ├── api/
│   │   └── main.py             # FastAPI endpoints: /upload, /review/{id}, /status/{id}, /report/{id}
│   └── ui/
│       └── app.py              # Streamlit prototype
├── alembic/
│   ├── env.py
│   └── versions/               # migrations (SQLite default)
├── scripts/
│   └── generate_samples.py     # generates report_good.docx + report_bad.docx
├── samples/                    # generated test documents (auto-created)
└── tests/
    ├── __init__.py
    ├── conftest.py               # session-scoped fixtures (good_docx, bad_docx, good_doc, bad_doc)
    ├── test_template_validator.py   # 3 passing tests
    ├── test_formatting_validator.py # 3 passing tests
    └── test_policy_checker.py       # 2 passing tests
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
# For full features (LLM, OCR, embeddings):
pip install -r requirements-optional.txt
```

### 2. Environment

Copy `.env.example` to `.env` and fill in:

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxx          # required for LLM modules
ANTHROPIC_MODEL=claude-sonnet-4-6         # default, matches api endpoint
DATABASE_URL=sqlite:///./guest_lecture_review.db  # or PostgreSQL URL
LANGUAGETOOL_URL=https://api.languagetool.org/v2/check  # optional self-hosted
ENABLE_LLM=1                              # 0 to run rule-based only
ENABLE_EMBEDDINGS=1                       # 0 to skip embedding pass
SEMANTIC_THRESHOLD=0.35
```

### 3. Run the rule-based unit tests

```bash
python -m pytest tests -v   # 9 tests, all pass
```

### 4. Start the FastAPI back-end

```bash
uvicorn app.api.main:app --host 127.0.0.1 --port 8000
```

### 5. Run the Streamlit UI

```bash
streamlit run app/ui/app.py
```

Open `http://localhost:8501` in your browser.

- Upload a `.docx` or `.pdf` file.
- Click **Run Review**.
- Watch per-module progress badges (✅ done / ⏳ pending).
- When complete, view the **Score Card** with overall score, per-criterion breakdown, missing items, formatting errors, and 3‑5 improvement suggestions.

### 6. Rule‑only mode (no API key)

Set `ENABLE_LLM=0` in `.env`. The pipeline will use only the deterministic rule‑based modules (Template, Formatting, Policy). LLM modules (Completeness, Semantic quality, Grammar tone, Overall Quality) will gracefully skip with a note.

---

## Adding a New Academic Document Type

All checklist / spec / rubric data live in YAML under `config/`. To adapt the system for, e.g., **FDP (Faculty Development Programme)** reports:

1. Copy `config/required_fields.yaml` → `config/fdp_required_fields.yaml`.
2. Edit the `fields` list to include FDP‑specific keys (e.g., `fdp_title`, `workshop_objectives`).
3. Copy `config/formatting_spec.yaml` → `config/fdp_formatting_spec.yaml`; adjust font/spacing expectations.
4. Copy `config/policy_checklist.yaml` → `config/fdp_policy_checklist.yaml`; add/remove keyword items (budget, invitation, etc.).
5. Update `config/scoring_rubric.yaml` weights if the criterion distribution changes.
6. No Python code changes required — the validators/checkers read their configs at runtime.

To wire a new document type into the pipeline, add a node in `app/orchestration/graph.py` that reads from the new config, or extend the existing validators to check for optional extra keys.

---

## Swapping the LLM Provider

The system is designed to swap LLM providers with minimal changes:

1. **Implement a new client** with the same interface as `app.llm.client.ClaudeClient`:
   - `available` property
   - `complete(system, user)` async method returning the model's raw text
   - `structured(system, user)` async method returning parsed JSON (using your own `parse_json_response`)

2. **Replace the client instantiation** in `app/llm/__init__.py` (or pass it explicitly to the checkers).

3. **Update the env vars** (`ANTHROPIC_API_KEY` → your provider's key, `ANTHROPIC_MODEL` → model name).

4. **Optional**: Adjust the prompt templates in `app/llm/prompts.py` to match the new provider's message format (Anthropic `messages` format vs. OpenAI `chat.completions`).

The rule‑based modules (2, 3, 7) are completely provider‑agnostic and need no changes.

---

## End‑to‑End Flow (User View)

1. **Upload** a DOCX or PDF guest lecture report via Streamlit.
2. **Parser** module extracts: raw text by section, tables, images, fonts, sizes, styles, headers/footers, page count, margins → normalized JSON.
3. **Template Validator** (modules 2) checks required fields against YAML checklist → pass/fail per field + missing list.
4. **Formatting Validator** (module 3) compares font/size/headings/margins/etc. → pass/fail per rule with expected/actual.
5. **Completeness Checker** (module 4) → Claude → JSON of present/missing content items (event objective, speaker introduction, lecture summary, learning outcomes, student participation, conclusion).
6. **Semantic Quality Checker** (module 5) → LLM + embeddings: meaningful/non‑repetitive/aligned-with-title + cosine‑similarity mismatches.
7. **Grammar Checker** (module 6) → LanguageTool issues + optional LLM academic-tone notes.
8. **Policy Checker** (module 7) → config‑driven min pages, images, signatures, attached forms, etc.
9. **Scoring Agent** (module 8) → rubric‑weighted per-criterion scores + overall quality (LLM subjective) → final JSON report.
10. **Report** displayed: overall score (0‑100), grade, per-criterion breakdown, missing items, formatting errors, 3‑5 actionable suggestions.

---

## Test Documents

Two sample documents are generated automatically:

- `samples/report_good.docx` – fully compliant: Calibri 11, 1.15 spacing, 1‑inch margins, heading styles, page numbers (PAGE field), 3 centered images, styled table, bullets, all required fields + policy keywords present. Scores ~77 (B).
- `samples/report_bad.docx` – deliberate violations: Times New Roman 12, 2.0 spacing, 0.5‑inch margins, no headings, no header/footer/page numbers, one left‑aligned image, no tables, missing most required fields/policy keywords. Scores ~35 (F).

Unit tests validate the rule‑based modules against these fixtures.

---

## Additional Notes

- The prototype Streamlit UI polls the FastAPI `/status/{id}` endpoint every second; in production WebSockets or server‑sent events would be used for real‑time progress.
- The LangGraph checkpointer (`MemorySaver`) persists intermediate state between runs; the FastAPI `/review/{id}` endpoint can be called again to retry a failed module without re‑uploading.
- All per‑criterion scores are deterministic from module outputs; only the **Overall Quality** score (weight 15) uses the LLM subjectively.
- The system is fully unit‑tested for the three rule‑based modules (template, formatting, policy) with 9 passing pytest cases.
- For PostgreSQL production deployment, set `DATABASE_URL` to your PG connection string and run `alembic upgrade head` to apply migrations.