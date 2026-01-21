"""
Shared tool abstractions for MyCoder.

This module centralizes the base classes and enums so tool modules can import
the essentials without introducing import cycles through :mod:`tool_registry`.
"""

from abc import ABC
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ToolCategory(Enum):
    """Tool categories used by the registry and tool metadata."""

    FILE_OPERATIONS = "file_operations"
    GIT_OPERATIONS = "git_operations"
    TERMINAL_OPERATIONS = "terminal_operations"
    DATABASE_OPERATIONS = "database_operations"
    MEMORY_OPERATIONS = "memory_operations"
    RESEARCH_OPERATIONS = "research_operations"
    COMMUNICATION = "communication"
    SYSTEM_MONITORING = "system_monitoring"
    AI_OPERATIONS = "ai_operations"
    THERMAL_MANAGEMENT = "thermal_management"


class ToolAvailability(Enum):
    """Availability levels describing when a tool is permitted to run."""

    ALWAYS = "always"
    FULL_ONLY = "full_only"
    DEGRADED_PLUS = "degraded_plus"
    AUTONOMOUS_PLUS = "autonomous_plus"
    LOCAL_ONLY = "local_only"
    RECOVERY_ONLY = "recovery_only"


class ToolPriority(Enum):
    """Execution priority for competing tool requests."""

    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class ToolCapabilities:
    """Describes requirements that a tool enforces before running."""

    requires_network: bool = False
    requires_filesystem: bool = False
    requires_auth: bool = False
    requires_mcp: bool = False
    requires_thermal_safe: bool = False
    max_execution_time: int = 30
    resource_intensive: bool = False
    supports_streaming: bool = False
    supports_caching: bool = False


@dataclass
class ToolExecutionContext:
    """Context metadata supplied to tool executions."""

    mode: str
    working_directory: Optional[Path] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    thermal_status: Optional[Dict[str, Any]] = None
    network_status: Optional[Dict[str, Any]] = None
    resource_limits: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ToolResult:
    """Standardized result produced by any tool execution."""

    success: bool
    data: Any
    tool_name: str
    duration_ms: int
    error: Optional[str] = None
    warnings: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.metadata is None:
            self.metadata = {}


class BaseTool(ABC):
    """Minimal tool contract implemented by every registry tool."""

    def __init__(
        self,
        name: str,
        category: ToolCategory,
        availability: ToolAvailability,
        priority: ToolPriority,
        capabilities: ToolCapabilities,
    ):
        self.name = name
        self.category = category
        self.availability = availability
        self.priority = priority
        self.capabilities = capabilities
        self.execution_count = 0
        self.error_count = 0
        self.total_execution_time = 0
        self.last_execution = 0

    async def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """Execute the tool with the supplied context."""
        raise NotImplementedError("Tool execution not implemented.")

    async def validate_context(self, context: ToolExecutionContext) -> bool:
        """Return whether the tool can run in the given context."""
        raise NotImplementedError("Context validation not implemented.")

    def get_description(self) -> str:
        return f"{self.name} tool"

    def get_input_schema(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def to_anthropic_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.get_description(),
            "input_schema": self.get_input_schema(),
        }

    def to_gemini_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.get_description(),
            "parameters": self.get_input_schema(),
        }

    def can_execute_in_mode(self, mode: str) -> bool:
        """Check whether the tool is permitted in the given operational mode."""
        mode_mappings = {
            "FULL": [
                ToolAvailability.ALWAYS,
                ToolAvailability.FULL_ONLY,
                ToolAvailability.DEGRADED_PLUS,
                ToolAvailability.AUTONOMOUS_PLUS,
            ],
            "DEGRADED": [
                ToolAvailability.ALWAYS,
                ToolAvailability.DEGRADED_PLUS,
                ToolAvailability.AUTONOMOUS_PLUS,
            ],
            "AUTONOMOUS": [
                ToolAvailability.ALWAYS,
                ToolAvailability.AUTONOMOUS_PLUS,
                ToolAvailability.LOCAL_ONLY,
            ],
            "RECOVERY": [
                ToolAvailability.ALWAYS,
                ToolAvailability.RECOVERY_ONLY,
                ToolAvailability.LOCAL_ONLY,
            ],
        }
        allowed = mode_mappings.get(mode.upper(), [ToolAvailability.ALWAYS])
        return self.availability in allowed

    def get_metrics(self) -> Dict[str, Any]:
        """Return execution statistics and derived performance numbers."""
        avg_execution_time = (
            self.total_execution_time / self.execution_count
            if self.execution_count > 0
            else 0
        )
        success_rate = (
            (self.execution_count - self.error_count) / self.execution_count
            if self.execution_count > 0
            else 1.0
        )
        return {
            "name": self.name,
            "category": self.category.value,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "success_rate": success_rate,
            "avg_execution_time": avg_execution_time,
            "last_execution": self.last_execution,
        }
