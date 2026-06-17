"""
Python Wrapper - market strategy adapters.

Current role:
- expose legacy/transition execution adapters for compatibility paths
- expose local Skill bridge utilities
- keep FastAPI/SSE and upload services as auxiliary APIs

Boundary:
- python_wrapper is not the complex market-analysis orchestration brain.
- Complex task decisions belong to strategy-orchestrator.
- This package should stay as adapter, event bridge, upload service, and legacy API surface.
"""

from .workflow_ai_orchestrator import (
    OpenProseWorkflowOrchestrator,
    WorkflowContext,
    WorkflowEvent,
    StageStatus,
    run_market_analysis_ai,
)
from .skill_caller import SkillCaller, get_caller

__all__ = [
    "OpenProseWorkflowOrchestrator",
    "WorkflowContext",
    "WorkflowEvent",
    "StageStatus",
    "run_market_analysis_ai",
    "SkillCaller",
    "get_caller",
]

__version__ = "2.0.0"
