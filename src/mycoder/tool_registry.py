"""
FEI-Inspired Tool Registry for MyCoder v2.2.0

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
import os
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    from .mcp_connector import MCPConnector
except ImportError:
    try:
        from mcp_connector import MCPConnector  # type: ignore
    except ImportError:
        MCPConnector = None  # type: ignore
try:
    from .tools.edit_tool import EditTool
except ImportError:
    try:
        from tools.edit_tool import EditTool  # type: ignore
    except ImportError:
        EditTool = None  # type: ignore
try:
    from .tools.core import (
        BaseTool,
        ToolAvailability,
        ToolCapabilities,
        ToolCategory,
        ToolExecutionContext,
        ToolPriority,
        ToolResult,
    )
except ImportError:
    try:
        from tools.core import (  # type: ignore
            BaseTool,
            ToolAvailability,
            ToolCapabilities,
            ToolCategory,
            ToolExecutionContext,
            ToolPriority,
            ToolResult,
        )
    except ImportError as inner_exc:
        raise ImportError(
            "Unable to import tool core components required by tool_registry."
        ) from inner_exc

from .security import FileSecurityManager, SecurityError
from .self_evolve.failure_memory import AdvisoryResult, FailureMemory

logger = logging.getLogger(__name__)


class FileOperationTool(BaseTool):
    """File operation tool implementation"""

    def __init__(self, name: str, on_read: Optional[Callable[[str], None]] = None):
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
        self.on_read = on_read

    def get_description(self) -> str:
        if self.name == "file_read":
            return "Read file contents from disk."
        if self.name == "file_write":
            return "Write content to a file on disk."
        if self.name == "file_list":
            return "List files in a directory."
        return "File operation tool."

    def get_input_schema(self) -> Dict[str, Any]:
        if self.name == "file_read":
            return {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to file",
                    }
                },
                "required": ["path"],
            }
        if self.name == "file_write":
            return {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to file",
                    },
                    "content": {
                        "type": "string",
                        "description": "File content to write",
                    },
                },
                "required": ["path", "content"],
            }
        if self.name == "file_list":
            return {
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory path to list",
                    }
                },
            }
        return super().get_input_schema()

    async def execute(
        self,
        context: ToolExecutionContext,
        operation: str = "read",
        path: Optional[str] = None,
        content: Optional[str] = None,
        directory: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        """Execute file operation"""
        start_time = time.time()
        self.execution_count += 1

        try:
            if operation == "read" and self.name == "file_list":
                operation = "list"
            elif operation == "read" and self.name == "file_write":
                operation = "write"
            elif operation == "read" and self.name == "file_read":
                operation = "read"

            if operation not in {"read", "write", "list", "exists"}:
                raise ValueError(f"Unsupported operation: {operation}")

            if not path and directory:
                path = directory

            if not path:
                raise ValueError("File path is required")

            # Join with working directory if relative
            file_path_obj = Path(path)
            if context.working_directory and not file_path_obj.is_absolute():
                file_path_obj = context.working_directory / file_path_obj

            # Initialize Security Manager
            security = FileSecurityManager(working_directory=context.working_directory)

            try:
                # Securely resolve path (prevents traversal)
                file_path = security.validate_path(file_path_obj)
            except SecurityError as e:
                raise PermissionError(str(e))

            result_data = None

            if operation == "read":
                if file_path.exists():
                    result_data = file_path.read_text(encoding="utf-8")
                    if self.on_read:
                        self.on_read(str(file_path))
                else:
                    raise FileNotFoundError(f"File not found: {file_path}")

            elif operation == "write":
                if content is None:
                    raise ValueError("Content is required for write operation")
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding="utf-8")
                result_data = f"Written {len(content)} characters to {file_path}"
                # Mark file as read after successful write (allows immediate editing)
                if self.on_read:
                    self.on_read(str(file_path))

            elif operation == "list":
                if file_path.is_dir():
                    result_data = [str(item) for item in file_path.iterdir()]
                else:
                    raise ValueError(f"Path is not a directory: {file_path}")

            elif operation == "exists":
                result_data = file_path.exists()

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


class FileEditTool(BaseTool):
    """File edit tool implementation."""

    def __init__(self, name: str, edit_tool: EditTool):
        capabilities = ToolCapabilities(
            requires_filesystem=True, max_execution_time=10, supports_caching=False
        )
        super().__init__(
            name=name,
            category=ToolCategory.FILE_OPERATIONS,
            availability=ToolAvailability.ALWAYS,
            priority=ToolPriority.HIGH,
            capabilities=capabilities,
        )
        self.edit_tool = edit_tool

    def get_description(self) -> str:
        return (
            "Edit files using Search & Replace. "
            "Find unique old_string and replace with new_string. "
            "ALWAYS read the file first."
        )

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path to file",
                },
                "old_string": {
                    "type": "string",
                    "description": "Exact text to find (must be unique)",
                },
                "new_string": {
                    "type": "string",
                    "description": "Replacement text",
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace all occurrences (default false)",
                    "default": False,
                },
            },
            "required": ["path", "old_string", "new_string"],
        }

    async def execute(
        self,
        context: ToolExecutionContext,
        path: Optional[str] = None,
        old_string: Optional[str] = None,
        new_string: Optional[str] = None,
        replace_all: bool = False,
        **kwargs,
    ) -> ToolResult:
        start_time = time.time()
        self.execution_count += 1

        if not path or old_string is None or new_string is None:
            duration_ms = int((time.time() - start_time) * 1000)
            self.error_count += 1
            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                duration_ms=duration_ms,
                error='Usage: /edit <path> "old" "new" [--all]',
            )

        # Join with working directory if relative
        file_path_obj = Path(path)
        if context.working_directory and not file_path_obj.is_absolute():
            file_path_obj = context.working_directory / file_path_obj

        # Initialize Security Manager
        security = FileSecurityManager(working_directory=context.working_directory)

        try:
            # Securely resolve path
            file_path = security.validate_path(file_path_obj)
        except SecurityError as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.error_count += 1
            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                duration_ms=duration_ms,
                error=str(e),
            )

        edit_result = self.edit_tool.edit(
            str(file_path),
            old_string,
            new_string,
            replace_all=replace_all,
        )

        duration_ms = int((time.time() - start_time) * 1000)
        self.total_execution_time += duration_ms
        self.last_execution = time.time()

        if edit_result.success:
            return ToolResult(
                success=True,
                data=edit_result.message,
                tool_name=self.name,
                duration_ms=duration_ms,
                metadata={"path": str(file_path)},
            )

        self.error_count += 1
        return ToolResult(
            success=False,
            data=None,
            tool_name=self.name,
            duration_ms=duration_ms,
            error=edit_result.message,
        )

    async def validate_context(self, context: ToolExecutionContext) -> bool:
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
            if MCPConnector is None:
                raise Exception("MCP connector not available")

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
            thermal_script = os.environ.get("MYCODER_THERMAL_SCRIPT", "")
            if not thermal_script or not os.path.exists(thermal_script):
                return True  # Assume safe if no script configured

            process = await asyncio.create_subprocess_exec(
                thermal_script,
                "status",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=5.0
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except ProcessLookupError:
                    logger.debug("Thermal check process already exited before kill.")
                return True  # Fail open on timeout

            if process.returncode == 0:
                # If status contains "CRITICAL" or temperature warnings, block
                return "CRITICAL" not in stdout.decode().upper()

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
        self.failure_memory = FailureMemory()
        self._initialize_core_tools()

    def _initialize_core_tools(self):
        """Initialize core system tools"""

        # File operations
        edit_tool = EditTool(Path.cwd()) if EditTool else None
        if edit_tool:
            self.register_tool(FileEditTool("file_edit", edit_tool))
            file_read_tool = FileOperationTool(
                "file_read", on_read=edit_tool.mark_as_read
            )
            file_write_tool = FileOperationTool(
                "file_write", on_read=edit_tool.mark_as_read
            )
        else:
            file_read_tool = FileOperationTool("file_read")
            file_write_tool = FileOperationTool("file_write")
        self.register_tool(file_read_tool)
        self.register_tool(file_write_tool)
        self.register_tool(FileOperationTool("file_list"))

        # Speech recognition tool (v2.2.0)
        try:
            from .speech_tool import SpeechTool

            self.register_tool(SpeechTool())
            logger.info("Registered SpeechTool")
        except ImportError as e:
            logger.warning(f"SpeechTool not available: {e}")

        # Add more core tools as needed
        logger.info("Initialized core tools in registry")

    def register_tool(self, tool: BaseTool):
        """Register a new tool in the registry"""
        if tool.name in self.tools:
            logger.warning(f"Tool {tool.name} already registered, replacing")
            existing = self.tools[tool.name]
            if existing.category in self.categories:
                self.categories[existing.category] = [
                    name
                    for name in self.categories[existing.category]
                    if name != tool.name
                ]

        self.tools[tool.name] = tool

        # Organize by category
        if tool.category not in self.categories:
            self.categories[tool.category] = []
        self.categories[tool.category].append(tool.name)

        logger.info(f"Registered tool: {tool.name} ({tool.category.value})")

        # Emit registration event
        self._emit_event("tool_registered", {"tool": tool})

    def reset(self) -> None:
        """Reset registry state and re-register core tools."""
        self.tools = {}
        self.categories = {}
        self._initialize_core_tools()

    def get_available_tools(self) -> List[str]:
        """Get list of all available tool names"""
        return list(self.tools.keys())

    def list_tools_by_category(self, category: ToolCategory) -> List[str]:
        """Get tools in a specific category"""
        return self.categories.get(category, [])

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
        file_context = (
            context.metadata.get("file_context") if context.metadata else None
        )
        env_hash = FailureMemory.compute_env_snapshot_hash(
            working_directory=context.working_directory,
            file_context=file_context,
        )

        advisory = self.failure_memory.check_advisory(
            tool_name=tool_name, params=kwargs, env_snapshot_hash=env_hash
        )

        if advisory.result == AdvisoryResult.BLOCK:
            logger.warning(
                "Tool execution blocked by FailureMemory: %s", advisory.reason
            )
            return ToolResult(
                success=False,
                data=None,
                tool_name=tool_name,
                duration_ms=0,
                error=f"BLOCKED by FailureMemory: {advisory.reason}",
                metadata={
                    "advisory": advisory.result.value,
                    "retry_count": advisory.retry_count,
                },
            )

        if advisory.result == AdvisoryResult.WARN:
            logger.warning(
                "Tool execution warning from FailureMemory: %s", advisory.reason
            )
            self._emit_event(
                "failure_memory_warning",
                {
                    "tool_name": tool_name,
                    "advisory": advisory.result.value,
                    "reason": advisory.reason,
                    "context": context,
                },
            )

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

            if not result.success:
                self.failure_memory.record_failure(
                    tool_name=tool_name,
                    params=kwargs,
                    error_message=result.error or "Unknown error",
                    env_snapshot_hash=env_hash,
                )
            else:
                self.failure_memory.clear_failure(
                    tool_name=tool_name,
                    params=kwargs,
                    env_snapshot_hash=env_hash,
                )

            return result

        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")

            self.failure_memory.record_failure(
                tool_name=tool_name,
                params=kwargs,
                error_message=str(e),
                env_snapshot_hash=env_hash,
            )

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
            "priority": tool.priority.name.lower(),
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
