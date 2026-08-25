"""Prompt templates for LLM-backed modules (4, 5, 6, and the subjective part of 8)."""

COMPLETENESS_SYSTEM = (
    "You are an academic document reviewer for university guest lecture reports. "
    "You verify whether specific content sections are present and adequate. "
    "Reply with STRICT JSON only, no prose, no markdown fences."
)

COMPLETENESS_USER = """Analyze the guest lecture report below.

Required content items to verify (use exactly these names in your JSON keys):
- event_objective
- speaker_introduction
- lecture_summary
- learning_outcomes
- student_participation
- conclusion

Respond with this exact JSON shape:
{{"present": ["event_objective", ...], "missing": ["lecture_summary", ...],
  "notes": {{"event_objective": "brief evidence or adequacy comment", ...}}}}

Rules:
- "present" = the item clearly appears AND is adequately covered (at least a few sentences / clear evidence).
- If it appears but is only a single bare phrase with no substance, treat it as present but note it as thin in "notes".
- Do not invent content that is not in the document.

DOCUMENT:
{text}
"""

SEMANTIC_QUALITY_SYSTEM = (
    "You are an academic quality assessor. Evaluate the lecture summary of a "
    "guest lecture report. Reply with STRICT JSON only."
)

SEMANTIC_QUALITY_USER = """Evaluate the quality and coherence of this lecture summary
against its stated title.

Title: {title}
Summary:
{summary}

Respond with exactly:
{{"meaningful": true/false, "non_repetitive": true/false,
  "adequate_length": true/false, "aligned_with_title": true/false,
  "notes": "one or two sentences of justification"}}

Base each boolean only on the text provided.
"""

OVERALL_QUALITY_SYSTEM = (
    "You are the final reviewer in a guest lecture report scoring pipeline. "
    "Score the OVERALL QUALITY of the report on a 0..100 scale. "
    "Reply with STRICT JSON only."
)

OVERALL_QUALITY_USER = """Given the extracted report text and the automated module findings below,
rate the overall quality of this guest lecture report.

SCORE RUBRIC (0-100):
- 85-100: outstanding - comprehensive, well structured, clearly documented
- 70-84: good - most elements present, minor gaps
- 50-69: acceptable - several gaps, work needed
- 0-49: poor - major omissions or sloppy documentation

Report title: {title}
Module findings:
{module_summary}

REPORT TEXT (truncated):
{text}

Respond with exactly:
{{"score": <int 0-100>, "rationale": "one or two sentences"}}
"""

GRAMMAR_TONE_SYSTEM = (
    "You are an academic writing advisor. Assess the academic tone of a guest "
    "lecture report and give brief improvement notes. Reply with STRICT JSON only."
)

GRAMMAR_TONE_USER = """Assess the academic tone of this report text.
Reply with exactly:
{{"tone_assessment": "good" | "acceptable" | "needs work",
  "notes": "2-3 concrete suggestions for academic tone"}}

TEXT:
{text}
"""


def _truncate(text: str, limit: int = 18000) -> str:
    return text[:limit] if len(text) > limit else text


def completeness_prompt(text: str) -> tuple[str, str]:
    return COMPLETENESS_SYSTEM, COMPLETENESS_USER.format(text=_truncate(text))


def semantic_quality_prompt(title: str, summary: str) -> tuple[str, str]:
    return (
        SEMANTIC_QUALITY_SYSTEM,
        SEMANTIC_QUALITY_USER.format(
            title=title or "(untitled)", summary=_truncate(summary or "(no summary extracted)")
        ),
    )


def overall_quality_prompt(title: str, module_summary: str, text: str) -> tuple[str, str]:
    return (
        OVERALL_QUALITY_SYSTEM,
        OVERALL_QUALITY_USER.format(
            title=title or "(untitled)",
            module_summary=module_summary,
            text=_truncate(text),
        ),
    )


def grammar_tone_prompt(text: str) -> tuple[str, str]:
    return GRAMMAR_TONE_SYSTEM, GRAMMAR_TONE_USER.format(text=_truncate(text))