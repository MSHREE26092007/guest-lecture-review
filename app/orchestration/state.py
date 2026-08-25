"""Module 8 (continued): LangGraph orchestration state.

Defines the shared PipelineState model that is passed between nodes.
Each node reads/writes typed fields and updates its status flag.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel

from app.schemas.modules import (
    TemplateCheckResult,
    FormattingCheckResult,
    CompletenessResult,
    SemanticResult,
    GrammarResult,
    PolicyResult,
    FinalReport,
    ModuleResult,
)
from app.schemas.document import ParsedDocument


class ModuleStatus(str, Enum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"


class PipelineState(BaseModel):
    """Shared state passed between LangGraph nodes."""

    submission_id: str = ""
    filename: str = ""
    parsed_document: Optional[ParsedDocument] = None
    status: ModuleStatus = ModuleStatus.pending

    # Module results
    template_result: Optional[TemplateCheckResult] = None
    formatting_result: Optional[FormattingCheckResult] = None
    completeness_result: Optional[CompletenessResult] = None
    semantic_result: Optional[SemanticResult] = None
    grammar_result: Optional[GrammarResult] = None
    policy_result: Optional[PolicyResult] = None

    # Module execution status (used for skip/retry)
    template_status: ModuleStatus = ModuleStatus.pending
    formatting_status: ModuleStatus = ModuleStatus.pending
    completeness_status: ModuleStatus = ModuleStatus.pending
    semantic_status: ModuleStatus = ModuleStatus.pending
    grammar_status: ModuleStatus = ModuleStatus.pending
    policy_status: ModuleStatus = ModuleStatus.pending

    # Scoring and report
    final_report: Optional[FinalReport] = None
    error: Optional[str] = None