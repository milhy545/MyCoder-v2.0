"""
FEI-Inspired Tool Registry for MyCoder v2.0

This module implements a centralized tool registry system inspired by the FEI project
architecture for managing and routing tools across different operational modes.

Features:
- Tool Registry Pattern for centralized management
- Service Layer Pattern for modular tool interfaces  
- Event-based tool execution and monitoring
- Intelligent tool routing based on context and capabilities
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Set
from pathlib import Path

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """Tool categories for organization and routing"""

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
    """Tool availability levels for different operational modes"""

    ALWAYS = "always"  # Available in all modes
    FULL_ONLY = "full_only"  # Only in FULL mode
    DEGRADED_PLUS = "degraded_plus"  # FULL and DEGRADED modes
    AUTONOMOUS_PLUS = "autonomous_plus"  # FULL, DEGRADED, AUTONOMOUS modes
    LOCAL_ONLY = "local_only"  # No network required
    RECOVERY_ONLY = "recovery_only"  # Emergency mode only


class ToolPriority(Enum):
    """Tool execution priority levels"""

    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class ToolCapabilities:
    """Capabilities and requirements for a tool"""

    requires_network: bool = False
    requires_filesystem: bool = False
    requires_auth: bool = False
    requires_mcp: bool = False
    requires_thermal_safe: bool = False  # Q9550 specific
    max_execution_time: int = 30  # seconds
    resource_intensive: bool = False
    supports_streaming: bool = False
    supports_caching: bool = False


@dataclass
class ToolExecutionContext:
    """Context for tool execution"""

    mode: str  # Operational mode
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
    """Standardized tool execution result"""

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
    """Base class for all tools in the registry"""

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

    @abstractmethod
    async def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """Execute the tool with given context"""
        pass

    @abstractmethod
    async def validate_context(self, context: ToolExecutionContext) -> bool:
        """Validate if tool can execute in given context"""
        pass

    def can_execute_in_mode(self, mode: str) -> bool:
        """Check if tool can execute in given operational mode"""
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
                ToolAvailability.LOCAL_ONLY,
                ToolAvailability.AUTONOMOUS_PLUS,
            ],
            "RECOVERY": [
                ToolAvailability.ALWAYS,
                ToolAvailability.RECOVERY_ONLY,
                ToolAvailability.LOCAL_ONLY,
            ],
        }

        return self.availability in mode_mappings.get(mode, [])

    def get_metrics(self) -> Dict[str, Any]:
        """Get tool execution metrics"""
        avg_execution_time = 0
        if self.execution_count > 0:
            avg_execution_time = self.total_execution_time / self.execution_count

        success_rate = 1.0
        if self.execution_count > 0:
            success_rate = (
                self.execution_count - self.error_count
            ) / self.execution_count

        return {
            "name": self.name,
            "category": self.category.value,
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "success_rate": success_rate,
            "avg_execution_time": avg_execution_time,
            "last_execution": self.last_execution,
        }


class FileOperationTool(BaseTool):
    """File operation tool implementation"""

    def __init__(self, name: str):
        capabilities = ToolCapabilities(
            requires_filesystem=True, max_execution_time=10, supports_caching=True
        )
        super().__init__(
            name=name,
            category=ToolCategory.FILE_OPERATIONS,
            availability=ToolAvailability.ALWAYS,
            priority=ToolPriority.HIGH,
            capabilities=capabilities,
        )

    async def execute(
        self,
        context: ToolExecutionContext,
        operation: str = "read",
        path: Optional[str] = None,
        content: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """Execute file operation"""
        start_time = time.time()
        self.execution_count += 1

        try:
            if not path:
                raise ValueError("File path is required")

            file_path = Path(path)
            if context.working_directory:
                file_path = context.working_directory / file_path

            result_data = None

            if operation == "read":
                if file_path.exists():
                    result_data = file_path.read_text(encoding="utf-8")
                else:
                    raise FileNotFoundError(f"File not found: {file_path}")

            elif operation == "write":
                if not content:
                    raise ValueError("Content is required for write operation")
                file_path.write_text(content, encoding="utf-8")
                result_data = f"Written {len(content)} characters to {file_path}"

            elif operation == "list":
                if file_path.is_dir():
                    result_data = [str(item) for item in file_path.iterdir()]
                else:
                    raise ValueError(f"Path is not a directory: {file_path}")

            elif operation == "exists":
                result_data = file_path.exists()

            else:
                raise ValueError(f"Unsupported operation: {operation}")

            duration_ms = int((time.time() - start_time) * 1000)
            self.total_execution_time += duration_ms
            self.last_execution = time.time()

            return ToolResult(
                success=True,
                data=result_data,
                tool_name=self.name,
                duration_ms=duration_ms,
                metadata={"operation": operation, "path": str(file_path)},
            )

        except Exception as e:
            self.error_count += 1
            duration_ms = int((time.time() - start_time) * 1000)

            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                duration_ms=duration_ms,
                error=str(e),
            )

    async def validate_context(self, context: ToolExecutionContext) -> bool:
        """Validate file operation context"""
        if self.capabilities.requires_filesystem:
            return (
                context.working_directory is not None
                and context.working_directory.exists()
            )
        return True


class MCPTool(BaseTool):
    """MCP (Model Control Protocol) tool implementation"""

    def __init__(self, name: str, mcp_tool_name: str):
        capabilities = ToolCapabilities(
            requires_network=True,
            requires_mcp=True,
            max_execution_time=60,
            resource_intensive=True,
        )
        super().__init__(
            name=name,
            category=ToolCategory.RESEARCH_OPERATIONS,
            availability=ToolAvailability.FULL_ONLY,
            priority=ToolPriority.NORMAL,
            capabilities=capabilities,
        )
        self.mcp_tool_name = mcp_tool_name

    async def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """Execute MCP tool"""
        start_time = time.time()
        self.execution_count += 1

        try:
            # Import MCP connector
            from .mcp_connector import MCPConnector

            mcp_connector = MCPConnector()

            # Check if MCP orchestrator is available
            if not await mcp_connector.is_orchestrator_available():
                raise Exception("MCP orchestrator not available")

            # Execute MCP tool
            result = await mcp_connector.execute_tool(
                tool_name=self.mcp_tool_name, **kwargs
            )

            duration_ms = int((time.time() - start_time) * 1000)
            self.total_execution_time += duration_ms
            self.last_execution = time.time()

            return ToolResult(
                success=result.get("success", False),
                data=result.get("result"),
                tool_name=self.name,
                duration_ms=duration_ms,
                metadata={"mcp_tool": self.mcp_tool_name},
            )

        except Exception as e:
            self.error_count += 1
            duration_ms = int((time.time() - start_time) * 1000)

            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                duration_ms=duration_ms,
                error=str(e),
            )

    async def validate_context(self, context: ToolExecutionContext) -> bool:
        """Validate MCP tool context"""
        # Check network status if available
        if context.network_status:
            return context.network_status.get("connected", False)
        return True


class ThermalAwareTool(BaseTool):
    """Thermal-aware tool for Q9550 system integration"""

    def __init__(self, name: str, category: ToolCategory):
        capabilities = ToolCapabilities(
            requires_thermal_safe=True, resource_intensive=True, max_execution_time=120
        )
        super().__init__(
            name=name,
            category=category,
            availability=ToolAvailability.LOCAL_ONLY,
            priority=ToolPriority.LOW,
            capabilities=capabilities,
        )

    async def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """Execute with thermal monitoring"""
        start_time = time.time()
        self.execution_count += 1

        try:
            # Check thermal status before execution
            thermal_safe = await self._check_thermal_status(context)
            if not thermal_safe:
                raise Exception("Thermal limits exceeded - execution blocked")

            # Execute the actual tool logic
            result_data = await self._execute_core_logic(context, **kwargs)

            duration_ms = int((time.time() - start_time) * 1000)
            self.total_execution_time += duration_ms
            self.last_execution = time.time()

            return ToolResult(
                success=True,
                data=result_data,
                tool_name=self.name,
                duration_ms=duration_ms,
                metadata={"thermal_safe": True},
            )

        except Exception as e:
            self.error_count += 1
            duration_ms = int((time.time() - start_time) * 1000)

            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                duration_ms=duration_ms,
                error=str(e),
            )

    async def _check_thermal_status(self, context: ToolExecutionContext) -> bool:
        """Check thermal status with PowerManagement integration"""
        try:
            if context.thermal_status:
                temp = context.thermal_status.get("cpu_temp", 0)
                return temp < 80  # Safe threshold for Q9550

            # Fallback: check PowerManagement system directly
            import subprocess

            result = subprocess.run(
                [
                    "/home/milhy777/Develop/Production/PowerManagement/scripts/performance_manager.sh",
                    "status",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                # If status contains "CRITICAL" or temperature warnings, block
                return "CRITICAL" not in result.stdout.upper()

            return True  # Assume safe if can't check

        except Exception as e:
            logger.warning(f"Thermal check failed: {e}")
            return True  # Assume safe on error

    async def _execute_core_logic(self, context: ToolExecutionContext, **kwargs) -> Any:
        """Override this method with actual tool logic"""
        return {"message": "Base thermal-aware tool executed"}

    async def validate_context(self, context: ToolExecutionContext) -> bool:
        """Validate thermal-aware context"""
        return await self._check_thermal_status(context)


class ToolRegistry:
    """FEI-inspired centralized tool registry"""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.categories: Dict[ToolCategory, List[str]] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self._initialize_core_tools()

    def _initialize_core_tools(self):
        """Initialize core system tools"""

        # File operations
        self.register_tool(FileOperationTool("file_read"))
        self.register_tool(FileOperationTool("file_write"))
        self.register_tool(FileOperationTool("file_list"))

        # Add more core tools as needed
        logger.info("Initialized core tools in registry")

    def register_tool(self, tool: BaseTool):
        """Register a new tool in the registry"""
        if tool.name in self.tools:
            logger.warning(f"Tool {tool.name} already registered, replacing")

        self.tools[tool.name] = tool

        # Organize by category
        if tool.category not in self.categories:
            self.categories[tool.category] = []
        self.categories[tool.category].append(tool.name)

        logger.info(f"Registered tool: {tool.name} ({tool.category.value})")

        # Emit registration event
        self._emit_event("tool_registered", {"tool": tool})

    def get_available_tools(self) -> List[str]:
        """Get list of all available tool names"""
        return list(self.tools.keys())

    def list_tools_by_category(self, category: ToolCategory) -> List[str]:
        """Get tools in a specific category"""
        return self.categories.get(category, [])

    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """Get information about a specific tool"""
        if tool_name not in self.tools:
            return {}

        tool = self.tools[tool_name]
        return {
            "name": tool.name,
            "category": tool.category.value,
            "description": tool.description,
            "capabilities": {
                "requires_thermal_safe": tool.capabilities.requires_thermal_safe,
                "resource_intensive": tool.capabilities.resource_intensive,
                "max_execution_time": tool.capabilities.max_execution_time,
                "requires_network": tool.capabilities.requires_network,
            },
            "stats": {
                "execution_count": tool.execution_count,
                "error_count": tool.error_count,
                "total_execution_time": tool.total_execution_time,
                "last_execution": tool.last_execution,
            },
        }

    def unregister_tool(self, tool_name: str):
        """Unregister a tool from the registry"""
        if tool_name not in self.tools:
            return

        tool = self.tools[tool_name]
        del self.tools[tool_name]

        # Remove from category
        if tool.category in self.categories:
            self.categories[tool.category].remove(tool_name)
            if not self.categories[tool.category]:
                del self.categories[tool.category]

        logger.info(f"Unregistered tool: {tool_name}")
        self._emit_event("tool_unregistered", {"tool_name": tool_name})

    async def execute_tool(
        self, tool_name: str, context: ToolExecutionContext, **kwargs
    ) -> ToolResult:
        """Execute a tool with validation and monitoring"""

        if tool_name not in self.tools:
            return ToolResult(
                success=False,
                data=None,
                tool_name=tool_name,
                duration_ms=0,
                error=f"Tool {tool_name} not found",
            )

        tool = self.tools[tool_name]

        # Check if tool can execute in current mode
        if not tool.can_execute_in_mode(context.mode):
            return ToolResult(
                success=False,
                data=None,
                tool_name=tool_name,
                duration_ms=0,
                error=f"Tool {tool_name} not available in {context.mode} mode",
            )

        # Validate context
        try:
            if not await tool.validate_context(context):
                return ToolResult(
                    success=False,
                    data=None,
                    tool_name=tool_name,
                    duration_ms=0,
                    error=f"Context validation failed for {tool_name}",
                )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                tool_name=tool_name,
                duration_ms=0,
                error=f"Context validation error: {e}",
            )

        # Emit pre-execution event
        self._emit_event(
            "tool_pre_execution", {"tool_name": tool_name, "context": context}
        )

        # Execute tool
        try:
            result = await tool.execute(context, **kwargs)

            # Emit post-execution event
            self._emit_event(
                "tool_post_execution",
                {"tool_name": tool_name, "result": result, "context": context},
            )

            return result

        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")

            error_result = ToolResult(
                success=False,
                data=None,
                tool_name=tool_name,
                duration_ms=0,
                error=f"Execution error: {e}",
            )

            self._emit_event(
                "tool_execution_error",
                {"tool_name": tool_name, "error": error_result, "context": context},
            )

            return error_result

    def get_tools_for_mode(self, mode: str) -> List[str]:
        """Get list of tools available for given mode"""
        available_tools = []
        for tool_name, tool in self.tools.items():
            if tool.can_execute_in_mode(mode):
                available_tools.append(tool_name)
        return available_tools

    def get_tools_by_category(self, category: ToolCategory) -> List[str]:
        """Get tools by category"""
        return self.categories.get(category, [])

    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a tool"""
        if tool_name not in self.tools:
            return None

        tool = self.tools[tool_name]
        return {
            "name": tool.name,
            "category": tool.category.value,
            "availability": tool.availability.value,
            "priority": tool.priority.value,
            "capabilities": {
                "requires_network": tool.capabilities.requires_network,
                "requires_filesystem": tool.capabilities.requires_filesystem,
                "requires_auth": tool.capabilities.requires_auth,
                "requires_mcp": tool.capabilities.requires_mcp,
                "requires_thermal_safe": tool.capabilities.requires_thermal_safe,
                "max_execution_time": tool.capabilities.max_execution_time,
                "resource_intensive": tool.capabilities.resource_intensive,
                "supports_streaming": tool.capabilities.supports_streaming,
                "supports_caching": tool.capabilities.supports_caching,
            },
            "metrics": tool.get_metrics(),
        }

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get comprehensive registry statistics"""
        total_tools = len(self.tools)
        category_counts = {
            cat.value: len(tools) for cat, tools in self.categories.items()
        }

        total_executions = sum(tool.execution_count for tool in self.tools.values())
        total_errors = sum(tool.error_count for tool in self.tools.values())

        return {
            "total_tools": total_tools,
            "categories": category_counts,
            "total_executions": total_executions,
            "total_errors": total_errors,
            "success_rate": (total_executions - total_errors)
            / max(total_executions, 1),
        }

    def add_event_handler(self, event_type: str, handler: Callable):
        """Add event handler for tool events"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit event to registered handlers"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(event_type, data)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")


# Global registry instance
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry
