"""Agent orchestration system inspired by Claude Code CLI."""

from .base import BaseAgent, AgentResult, AgentType
from .explore import ExploreAgent
from .plan import PlanAgent
from .bash import BashAgent
from .general import GeneralPurposeAgent
from .orchestrator import AgentOrchestrator

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
