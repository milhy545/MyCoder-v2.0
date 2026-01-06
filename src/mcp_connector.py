"""
MCP Orchestrator Connector

Connects MyCoder adaptive modes system with the existing MCP orchestrator
running on 192.168.0.58:8020 for enhanced tool capabilities and data persistence.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiohttp

try:
    from .adaptive_modes import OperationalMode, ClaudeNetworkError
except ImportError:
    from adaptive_modes import OperationalMode, ClaudeNetworkError  # type: ignore

logger = logging.getLogger(__name__)


class MCPConnector:
    """
    Connector for MCP orchestrator integration with adaptive modes.

    Provides intelligent tool routing and data management based on
    current operational mode and service availability.
    """

    def __init__(
        self,
        orchestrator_url: str = "http://192.168.0.58:8020",
        auto_start_local: Optional[bool] = None,
        local_host: Optional[str] = None,
        local_port: Optional[int] = None,
        local_data_dir: Optional[str] = None,
    ):
        self.orchestrator_url = orchestrator_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.available_tools: List[str] = []
        self.service_status: Dict[str, Any] = {}
        self.last_health_check: float = 0
        self.health_check_interval = 60  # Check every 60 seconds
        self.auto_start_local = (
            auto_start_local
            if auto_start_local is not None
            else self._env_bool("MYCODER_MCP_LOCAL_AUTOSTART", True)
        )
        self.local_host = local_host or os.getenv("MYCODER_MCP_LOCAL_HOST", "127.0.0.1")
        self.local_port = local_port or int(os.getenv("MYCODER_MCP_LOCAL_PORT", "8020"))
        self.local_data_dir = local_data_dir or os.getenv("MYCODER_MCP_LOCAL_DATA_DIR")
        self.local_server = None
        self._local_server_url = f"http://{self.local_host}:{self.local_port}"

    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)

        # Initial health check
        await self.check_services_health()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
        await self._stop_local_server()

    async def check_services_health(self) -> Dict[str, Any]:
        """Check health of all MCP services."""
        if not self.session:
            return {}

        try:
            await self._ensure_orchestrator()
            # Get service status from orchestrator
            async with self.session.get(
                f"{self.orchestrator_url}/services"
            ) as response:
                if response.status == 200:
                    self.service_status = await response.json()

                    # Extract available tools from all services
                    self.available_tools = []
                    zen_services = self.service_status.get("zen_coordinator", {}).get(
                        "services", {}
                    )

                    for service_name, service_info in zen_services.items():
                        if (
                            isinstance(service_info, dict)
                            and service_info.get("status") == "running"
                        ):
                            tools = service_info.get("tools", [])
                            self.available_tools.extend(tools)

                    self.last_health_check = asyncio.get_event_loop().time()
                    logger.info(
                        f"MCP health check: {len(self.available_tools)} tools available from "
                        f"{len(zen_services)} services"
                    )

                    return self.service_status
                else:
                    logger.warning(f"MCP health check failed: HTTP {response.status}")
                    return {}

        except Exception as e:
            logger.error(f"MCP health check error: {e}")
            return {}

    async def _ensure_orchestrator(self) -> None:
        if not self.session:
            return

        if await self.test_connection():
            return

        if not self.auto_start_local:
            return

        try:
            await self._start_local_server()
            self.orchestrator_url = self._local_server_url
            if await self.test_connection():
                logger.info("Using local MCP server at %s", self._local_server_url)
            else:
                logger.warning(
                    "Local MCP server not reachable at %s", self._local_server_url
                )
        except Exception as exc:
            logger.warning("Failed to start local MCP server: %s", exc)

    async def _start_local_server(self) -> None:
        if self.local_server:
            return
        try:
            from .local_mcp_server import LocalMCPServer
        except Exception:
            from local_mcp_server import LocalMCPServer  # type: ignore

        data_dir = (
            Path(self.local_data_dir).expanduser() if self.local_data_dir else None
        )
        self.local_server = LocalMCPServer(
            host=self.local_host, port=self.local_port, data_dir=data_dir
        )
        await self.local_server.start()

    async def _stop_local_server(self) -> None:
        if self.local_server:
            await self.local_server.stop()
            self.local_server = None

    def _env_bool(self, name: str, default: bool) -> bool:
        value = os.getenv(name)
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def _is_local_url(self, url: str) -> bool:
        parsed = urlparse(url)
        host = parsed.hostname or ""
        return host in {"localhost", "127.0.0.1", "::1", self.local_host}

    async def get_available_tools_for_mode(self, mode: OperationalMode) -> List[str]:
        """Get available tools filtered by operational mode."""
        # Refresh health check if needed
        current_time = asyncio.get_event_loop().time()
        if current_time - self.last_health_check > self.health_check_interval:
            await self.check_services_health()

        # Filter tools based on mode
        if mode == OperationalMode.FULL:
            # All available tools
            return self.available_tools

        elif mode == OperationalMode.DEGRADED:
            # Essential tools only
            essential_tools = [
                "file_read",
                "file_write",
                "file_list",
                "file_search",
                "git_status",
                "git_commit",
                "git_diff",
                "terminal_exec",
                "shell_command",
                "store_memory",
                "search_memories",
            ]
            return [tool for tool in self.available_tools if tool in essential_tools]

        elif mode == OperationalMode.AUTONOMOUS:
            # Basic tools only
            basic_tools = [
                "file_read",
                "file_write",
                "file_list",
                "terminal_exec",
                "shell_command",
            ]
            return [tool for tool in self.available_tools if tool in basic_tools]

        else:  # RECOVERY
            # File operations only
            return ["file_read", "file_write", "file_list"]

    async def call_mcp_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        mode: OperationalMode,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        Call an MCP tool through the orchestrator with mode-aware handling.

        Args:
            tool_name: Name of the MCP tool to call
            arguments: Arguments to pass to the tool
            mode: Current operational mode for error handling
            timeout: Request timeout in seconds

        Returns:
            Dict containing tool response or error information
        """
        if not self.session:
            return {
                "success": False,
                "error": "MCP connector not initialized",
                "fallback_suggestion": "use_local_fallback",
            }

        await self._ensure_orchestrator()

        # Check if tool is available in current mode
        available_tools = await self.get_available_tools_for_mode(mode)
        if tool_name not in available_tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not available in {mode.value} mode",
                "available_tools": available_tools,
                "fallback_suggestion": (
                    "use_available_tool" if available_tools else "degrade_mode"
                ),
            }

        # Prepare request payload
        payload = {"tool": tool_name, "arguments": arguments}

        # Add mode-specific metadata
        payload["metadata"] = {
            "mode": mode.value,
            "timeout": timeout,
            "client": "mycoder_adaptive",
        }

        try:
            # Make request with appropriate timeout
            request_timeout = aiohttp.ClientTimeout(total=timeout)
            async with self.session.post(
                f"{self.orchestrator_url}/mcp", json=payload, timeout=request_timeout
            ) as response:

                if response.status == 200:
                    try:
                        result = await response.json()
                        return {
                            "success": True,
                            "result": result,
                            "tool": tool_name,
                            "mode": mode.value,
                        }
                    except Exception as parse_error:
                        # Handle non-JSON responses
                        text_result = await response.text()
                        return {
                            "success": True,
                            "result": {"content": text_result},
                            "tool": tool_name,
                            "mode": mode.value,
                            "note": "text_response",
                        }

                elif response.status == 502:
                    # Service error - suggest mode degradation
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"MCP service error: {error_text}",
                        "status_code": 502,
                        "fallback_suggestion": (
                            "degrade_mode"
                            if mode != OperationalMode.RECOVERY
                            else "use_local_fallback"
                        ),
                    }

                elif response.status == 400:
                    # Bad request - tool/args issue
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Bad request: {error_text}",
                        "status_code": 400,
                        "fallback_suggestion": "use_local_fallback",
                    }

                else:
                    # Other HTTP errors
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "status_code": response.status,
                        "fallback_suggestion": "retry_or_degrade",
                    }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"MCP tool call timeout after {timeout}s",
                "tool": tool_name,
                "fallback_suggestion": (
                    "retry_with_longer_timeout" if timeout < 60 else "degrade_mode"
                ),
            }

        except Exception as e:
            logger.error(f"MCP tool call error: {e}")
            return {
                "success": False,
                "error": f"MCP connection error: {str(e)}",
                "tool": tool_name,
                "fallback_suggestion": (
                    "degrade_mode"
                    if mode != OperationalMode.RECOVERY
                    else "use_local_fallback"
                ),
            }

    async def store_memory(
        self,
        content: str,
        memory_type: str = "interaction",
        importance: float = 0.5,
        mode: OperationalMode = OperationalMode.FULL,
    ) -> Dict[str, Any]:
        """Store memory through MCP memory service."""
        return await self.call_mcp_tool(
            "store_memory",
            {"content": content, "type": memory_type, "importance": importance},
            mode,
        )

    async def search_memories(
        self, query: str, limit: int = 5, mode: OperationalMode = OperationalMode.FULL
    ) -> Dict[str, Any]:
        """Search memories through MCP memory service."""
        return await self.call_mcp_tool(
            "search_memories", {"query": query, "limit": limit}, mode
        )

    async def read_file(self, file_path: str, mode: OperationalMode) -> Dict[str, Any]:
        """Read file through MCP filesystem service."""
        return await self.call_mcp_tool("file_read", {"path": file_path}, mode)

    async def write_file(
        self, file_path: str, content: str, mode: OperationalMode
    ) -> Dict[str, Any]:
        """Write file through MCP filesystem service."""
        return await self.call_mcp_tool(
            "file_write", {"path": file_path, "content": content}, mode
        )

    async def execute_command(
        self,
        command: str,
        working_dir: Optional[str] = None,
        mode: OperationalMode = OperationalMode.FULL,
    ) -> Dict[str, Any]:
        """Execute command through MCP terminal service."""
        args = {"command": command}
        if working_dir:
            args["working_dir"] = working_dir

        return await self.call_mcp_tool("terminal_exec", args, mode)

    async def git_status(self, repo_path: str, mode: OperationalMode) -> Dict[str, Any]:
        """Get git status through MCP git service."""
        return await self.call_mcp_tool("git_status", {"repo_path": repo_path}, mode)

    async def research_query(self, query: str, mode: OperationalMode) -> Dict[str, Any]:
        """Perform research query through MCP research service."""
        if mode in [OperationalMode.AUTONOMOUS, OperationalMode.RECOVERY]:
            return {
                "success": False,
                "error": "Research not available in offline modes",
                "fallback_suggestion": "use_local_resources",
            }

        return await self.call_mcp_tool("research_query", {"query": query}, mode)

    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status."""
        return {
            "orchestrator_url": self.orchestrator_url,
            "last_health_check": self.last_health_check,
            "available_tools": self.available_tools,
            "services": self.service_status,
            "health_check_interval": self.health_check_interval,
            "local_server": {
                "auto_start": self.auto_start_local,
                "enabled": self.local_server is not None,
                "url": self._local_server_url,
            },
        }

    async def test_connection(self) -> bool:
        """Test connection to MCP orchestrator."""
        try:
            if not self.session:
                return False

            async with self.session.get(f"{self.orchestrator_url}/health") as response:
                return response.status == 200

        except Exception as e:
            logger.debug(f"MCP connection test failed: {e}")
            return False


class MCPToolRouter:
    """
    Smart router for MCP tool calls with mode-aware fallbacks.

    Routes tool calls to appropriate services based on current mode
    and provides intelligent fallback strategies when services fail.
    """

    def __init__(self, connector: MCPConnector):
        self.connector = connector
        self.tool_mappings = {
            # File operations
            "read_file": "file_read",
            "write_file": "file_write",
            "list_files": "file_list",
            "search_files": "file_search",
            "analyze_file": "file_analyze",
            # Git operations
            "git_status": "git_status",
            "git_commit": "git_commit",
            "git_push": "git_push",
            "git_diff": "git_diff",
            "git_log": "git_log",
            # Terminal operations
            "execute": "terminal_exec",
            "shell": "shell_command",
            "system_info": "system_info",
            # Memory operations
            "store_memory": "store_memory",
            "search_memory": "search_memories",
            "get_context": "get_context",
            # Database operations
            "db_query": "db_query",
            "db_connect": "db_connect",
            "db_schema": "db_schema",
            # Research operations
            "research": "research_query",
            "web_search": "perplexity_search",
            "transcribe": "transcribe_webm",
        }

    async def route_tool_call(
        self, tool_name: str, arguments: Dict[str, Any], mode: OperationalMode
    ) -> Dict[str, Any]:
        """
        Route tool call to appropriate MCP service with fallback handling.

        Args:
            tool_name: Friendly tool name (e.g., 'read_file')
            arguments: Tool arguments
            mode: Current operational mode

        Returns:
            Dict containing tool result or fallback information
        """
        # Map friendly name to MCP tool name
        mcp_tool_name = self.tool_mappings.get(tool_name, tool_name)

        # Execute tool call
        result = await self.connector.call_mcp_tool(mcp_tool_name, arguments, mode)

        # Handle fallbacks based on result
        if not result.get("success"):
            fallback_suggestion = result.get("fallback_suggestion")

            if fallback_suggestion == "degrade_mode":
                result["adaptive_action"] = "degrade_mode"
                result["reason"] = "MCP service unavailable"

            elif fallback_suggestion == "use_local_fallback":
                result["adaptive_action"] = "use_local_fallback"
                result["local_alternatives"] = self._get_local_alternatives(tool_name)

            elif fallback_suggestion == "retry_or_degrade":
                result["adaptive_action"] = "retry_with_backoff"
                result["retry_delay"] = 5

        return result

    def _get_local_alternatives(self, tool_name: str) -> List[str]:
        """Get local alternatives for failed MCP tools."""
        alternatives = {
            "read_file": ["pathlib.Path.read_text", "built-in file operations"],
            "write_file": ["pathlib.Path.write_text", "built-in file operations"],
            "list_files": ["pathlib.Path.iterdir", "os.listdir"],
            "execute": ["subprocess.run", "asyncio.create_subprocess_exec"],
            "git_status": ["subprocess git status", "local git commands"],
            "store_memory": ["local JSON storage", "sqlite database"],
            "search_memory": ["local text search", "grep equivalent"],
        }

        return alternatives.get(tool_name, ["manual fallback required"])
