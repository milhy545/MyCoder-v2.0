"""
MCP Bridge for MyCoder v2.1.1

Propojuje tool_registry s MCP (Model Context Protocol) serverem.
Umožňuje spouštět MCP tools jako BaseTool implementace.
"""

import asyncio
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import aiohttp

try:
    from .local_mcp_server import LocalMCPServer
    from .mcp_connector import MCPConnector
    from .tool_registry import (
        BaseTool,
        ToolAvailability,
        ToolCapabilities,
        ToolCategory,
        ToolExecutionContext,
        ToolPriority,
        ToolResult,
    )
except ImportError:
    from local_mcp_server import LocalMCPServer
    from mcp_connector import MCPConnector
    from tool_registry import (
        BaseTool,
        ToolAvailability,
        ToolCapabilities,
        ToolCategory,
        ToolExecutionContext,
        ToolPriority,
        ToolResult,
    )

logger = logging.getLogger(__name__)


class MCPBridge:
    """
    Bridge mezi tool_registry a MCP serverem.

    Poskytuje:
    - Automatické spuštění local MCP serveru pokud neběží
    - Registraci MCP tools jako BaseTool objektů
    - Volání MCP endpoints přes unified interface
    """

    def __init__(
        self,
        mcp_url: str = "http://127.0.0.1:8020",
        auto_start: bool = True,
        local_host: str = "127.0.0.1",
        local_port: int = 8020,
    ):
        """
        Args:
            mcp_url: URL MCP serveru
            auto_start: Automaticky spustit local server pokud neběží
            local_host: Host pro local server
            local_port: Port pro local server
        """
        self.mcp_url = mcp_url
        self.auto_start = auto_start
        self.local_host = local_host
        self.local_port = local_port

        self.mcp_connector: Optional[MCPConnector] = None
        self.local_server: Optional[LocalMCPServer] = None
        self.local_server_process: Optional[subprocess.Popen] = None
        self.session: Optional[aiohttp.ClientSession] = None

        # Cache MCP tools
        self.mcp_tools: Dict[str, Dict[str, Any]] = {}
        self.is_initialized = False

    async def initialize(self) -> bool:
        """
        Inicializuje MCP bridge.

        Returns:
            True pokud se podařilo připojit k MCP serveru
        """
        if self.is_initialized:
            return True

        try:
            # Vytvořit session
            if not self.session:
                timeout = aiohttp.ClientTimeout(total=10)
                self.session = aiohttp.ClientSession(timeout=timeout)

            # Zkusit připojení k MCP serveru
            if await self._check_mcp_health():
                logger.info(f"Connected to MCP server at {self.mcp_url}")
            elif self.auto_start:
                # Spustit local server
                success = await self.start_local_mcp()
                if not success:
                    logger.error("Failed to start local MCP server")
                    return False
            else:
                logger.warning("MCP server not available and auto_start is disabled")
                return False

            # Inicializovat MCP connector
            self.mcp_connector = MCPConnector(
                orchestrator_url=self.mcp_url,
                auto_start_local=False,  # Už jsme spustili
            )

            # Načíst dostupné tools
            await self._load_available_tools()

            self.is_initialized = True
            return True

        except Exception as e:
            logger.error(f"Error initializing MCP bridge: {e}")
            return False

    async def start_local_mcp(self) -> bool:
        """
        Spustí local MCP server.

        Returns:
            True pokud se podařilo spustit server
        """
        try:
            # Check if already running
            if await self._check_mcp_health():
                logger.info("MCP server already running")
                return True

            logger.info("Starting local MCP server...")

            # Spustit server v subprocess
            # Najít cestu k local_mcp_server.py
            module_dir = Path(__file__).parent
            server_script = module_dir / "local_mcp_server.py"

            if not server_script.exists():
                logger.error(f"MCP server script not found: {server_script}")
                return False

            # Spustit jako subprocess
            self.local_server_process = subprocess.Popen(
                [
                    sys.executable,
                    str(server_script),
                    "--host",
                    self.local_host,
                    "--port",
                    str(self.local_port),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            # Počkat až server naběhne (max 5 sekund)
            for i in range(10):
                await asyncio.sleep(0.5)
                if await self._check_mcp_health():
                    logger.info(f"Local MCP server started on {self.mcp_url}")
                    return True

            logger.error("Local MCP server failed to start within timeout")
            return False

        except Exception as e:
            logger.error(f"Error starting local MCP server: {e}")
            return False

    async def stop_local_mcp(self) -> None:
        """Zastaví local MCP server"""
        if self.local_server:
            await self.local_server.stop()
            self.local_server = None

        if self.local_server_process:
            self.local_server_process.terminate()
            try:
                self.local_server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.local_server_process.kill()
            self.local_server_process = None

    async def _check_mcp_health(self) -> bool:
        """
        Zkontroluje zda MCP server běží.

        Returns:
            True pokud server odpovídá
        """
        if not self.session:
            return False

        try:
            async with self.session.get(f"{self.mcp_url}/health") as response:
                return response.status == 200
        except Exception:
            return False

    async def _load_available_tools(self) -> None:
        """Načte seznam dostupných MCP tools"""
        if not self.session:
            return

        try:
            async with self.session.get(f"{self.mcp_url}/services") as response:
                if response.status == 200:
                    data = await response.json()

                    services = data
                    if "zen_coordinator" in data:
                        services = data.get("zen_coordinator", {}).get("services", {})

                    # Extrahovat tools z různých služeb
                    for service_name, service_info in services.items():
                        if isinstance(service_info, dict):
                            tools = service_info.get("tools", [])
                            for tool_name in tools:
                                self.mcp_tools[tool_name] = {
                                    "service": service_name,
                                    "name": tool_name,
                                }

                    logger.info(
                        "Loaded %s MCP tools from %s services",
                        len(self.mcp_tools),
                        len(services),
                    )

        except Exception as e:
            logger.error(f"Error loading MCP tools: {e}")

    async def call_mcp_tool(
        self, tool_name: str, args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Zavolá MCP tool přes MCP endpoint.

        Args:
            tool_name: Název nástroje (např. "file_read")
            args: Argumenty pro nástroj

        Returns:
            Výsledek z MCP serveru
        """
        if not self.session:
            return {"success": False, "error": "MCP bridge not initialized"}

        try:
            payload = {"tool": tool_name, "arguments": args, "args": args}

            async with self.session.post(
                f"{self.mcp_url}/mcp", json=payload
            ) as response:
                result = await response.json()
                if "success" in result:
                    return result
                if "error" in result:
                    return {"success": False, "error": result.get("error")}
                return {"success": True, "data": result}

        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return {"success": False, "error": str(e)}

    async def register_mcp_tools_in_registry(self, tool_registry) -> None:
        """
        Zaregistruje MCP tools jako BaseTool objekty v tool_registry.

        Args:
            tool_registry: Instance ToolRegistry
        """
        if not self.is_initialized:
            await self.initialize()

        # Vytvořit BaseTool wrappery pro každý MCP tool
        skip_tools = {"file_read", "file_write", "file_list", "file_edit"}
        for tool_name, tool_info in self.mcp_tools.items():
            if tool_name in skip_tools and tool_name in tool_registry.tools:
                continue
            mcp_tool = self._create_mcp_tool_wrapper(tool_name, tool_info)
            tool_registry.register_tool(mcp_tool)

        logger.info(f"Registered {len(self.mcp_tools)} MCP tools in registry")

    def _create_mcp_tool_wrapper(
        self, tool_name: str, tool_info: Dict[str, Any]
    ) -> BaseTool:
        """
        Vytvoří BaseTool wrapper pro MCP tool.

        Args:
            tool_name: Název nástroje
            tool_info: Info o nástroji

        Returns:
            BaseTool instance
        """
        # Mapování MCP tools na kategorie
        category_map = {
            "file_read": ToolCategory.FILE_OPERATIONS,
            "file_write": ToolCategory.FILE_OPERATIONS,
            "file_list": ToolCategory.FILE_OPERATIONS,
            "file_search": ToolCategory.FILE_OPERATIONS,
            "terminal_exec": ToolCategory.TERMINAL_OPERATIONS,
            "shell_command": ToolCategory.TERMINAL_OPERATIONS,
            "system_info": ToolCategory.SYSTEM_MONITORING,
            "git_status": ToolCategory.GIT_OPERATIONS,
            "git_diff": ToolCategory.GIT_OPERATIONS,
            "git_log": ToolCategory.GIT_OPERATIONS,
            "store_memory": ToolCategory.MEMORY_OPERATIONS,
            "search_memories": ToolCategory.MEMORY_OPERATIONS,
        }

        category = category_map.get(tool_name, ToolCategory.TERMINAL_OPERATIONS)

        return MCPToolWrapper(
            name=tool_name,
            category=category,
            mcp_bridge=self,
            tool_info=tool_info,
        )

    async def close(self) -> None:
        """Zavře MCP bridge a ukončí resources"""
        if self.session:
            await self.session.close()
            self.session = None

        await self.stop_local_mcp()

        self.is_initialized = False


class MCPToolWrapper(BaseTool):
    """BaseTool wrapper pro MCP tool"""

    def __init__(
        self,
        name: str,
        category: ToolCategory,
        mcp_bridge: MCPBridge,
        tool_info: Dict[str, Any],
    ):
        super().__init__(
            name=name,
            category=category,
            availability=ToolAvailability.ALWAYS,
            priority=ToolPriority.NORMAL,
            capabilities=ToolCapabilities(
                requires_network=False,  # Local MCP server
                requires_filesystem=category == ToolCategory.FILE_OPERATIONS,
                max_execution_time=30,
            ),
        )
        self.mcp_bridge = mcp_bridge
        self.tool_info = tool_info

    async def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """Spustí MCP tool přes bridge"""
        start_time = time.time()

        try:
            # Volat MCP tool
            result = await self.mcp_bridge.call_mcp_tool(self.name, kwargs)

            duration_ms = int((time.time() - start_time) * 1000)

            if result.get("success", False):
                return ToolResult(
                    success=True,
                    data=result.get("data", result),
                    tool_name=self.name,
                    duration_ms=duration_ms,
                )
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    tool_name=self.name,
                    duration_ms=duration_ms,
                    error=result.get("error", "Unknown error"),
                )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                duration_ms=duration_ms,
                error=str(e),
            )

    async def validate_context(self, context: ToolExecutionContext) -> bool:
        """Validuje zda tool může běžet v daném kontextu"""
        # MCP tools jsou obecně vždycky dostupné
        return True
