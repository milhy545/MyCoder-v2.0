"""Agent orchestration system inspired by Claude Code CLI."""

from .base import AgentResult, AgentType, BaseAgent
from .bash import BashAgent
from .explore import ExploreAgent
from .general import GeneralPurposeAgent
from .orchestrator import AgentOrchestrator
from .plan import PlanAgent

__all__ = [
    "BaseAgent",
    "AgentResult",
    "AgentType",
    "ExploreAgent",
    "PlanAgent",
    "BashAgent",
    "GeneralPurposeAgent",
    "AgentOrchestrator",
]
