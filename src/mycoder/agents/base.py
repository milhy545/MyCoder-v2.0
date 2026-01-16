"""Base classes for agent orchestration."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class AgentType(Enum):
    EXPLORE = "explore"
    PLAN = "plan"
    BASH = "bash"
    GENERAL = "general"


@dataclass
class AgentResult:
    success: bool
    content: str
    agent_type: AgentType
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self, coder, working_directory: Path) -> None:
        self.coder = coder
        self.working_dir = working_directory
        self.context: List[Dict[str, Any]] = []

    @property
    @abstractmethod
    def agent_type(self) -> AgentType:
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def execute(self, task: str, context: Dict[str, Any] = None) -> AgentResult:
        raise NotImplementedError

    def add_context(self, item: Dict[str, Any]) -> None:
        self.context.append(item)
