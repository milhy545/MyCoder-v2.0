"""
Tool Execution Orchestrator for MyCoder v2.1.1

Koordinuje exekuci nástrojů mezi CLI, tool_registry a MCP serverem.
Poskytuje inteligentní routing a AI-assisted tool execution.
"""

import asyncio
import logging
import time
from urllib.parse import urlparse
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

try:
    from .command_parser import Command, CommandParser
    from .mcp_bridge import MCPBridge
    from .tool_registry import ToolExecutionContext, ToolResult, ToolRegistry
except ImportError:
    from command_parser import Command, CommandParser
    from mcp_bridge import MCPBridge
    from tool_registry import ToolExecutionContext, ToolResult, ToolRegistry

if TYPE_CHECKING:
    from .enhanced_mycoder_v2 import EnhancedMyCoderV2

logger = logging.getLogger(__name__)


class ToolExecutionOrchestrator:
    """
    Orchestrátor pro exekuci nástrojů.

    Zodpovědnosti:
    - Routing příkazů na správné tools
    - Validace execution context
    - Volání tools přes tool_registry
    - AI-assisted tool execution
    - Error handling a recovery
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        mcp_bridge: MCPBridge,
        ai_client: "EnhancedMyCoderV2",
    ):
        """
        Args:
            tool_registry: Registry nástrojů
            mcp_bridge: Bridge k MCP serveru
            ai_client: AI klient pro assisted execution
        """
        self.tool_registry = tool_registry
        self.mcp_bridge = mcp_bridge
        self.ai_client = ai_client
        self.command_parser = CommandParser()

        # Execution statistics
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0

    async def execute_command(
        self, command: Command, context: ToolExecutionContext
    ) -> ToolResult:
        """
        Spustí command jako tool.

        Args:
            command: Parsovaný příkaz
            context: Execution context

        Returns:
            ToolResult s výsledkem exekuce
        """
        start_time = time.time()
        self.total_executions += 1

        try:
            logger.info(
                f"Executing command: {command.tool} with args: {command.args}"
            )

            # Najít tool v registry
            tool = self.tool_registry.tools.get(command.tool)

            if not tool:
                # Tool není v registry - možná je to MCP tool
                logger.warning(
                    f"Tool '{command.tool}' not found in registry, trying MCP..."
                )
                result = await self._execute_mcp_tool_directly(
                    command.tool, command.args
                )

                if result.success:
                    self.successful_executions += 1
                else:
                    self.failed_executions += 1

                return result

            # Validovat kontext
            can_execute = await tool.validate_context(context)
            if not can_execute:
                duration_ms = int((time.time() - start_time) * 1000)
                self.failed_executions += 1
                return ToolResult(
                    success=False,
                    data=None,
                    tool_name=command.tool,
                    duration_ms=duration_ms,
                    error=f"Tool '{command.tool}' cannot execute in current context",
                )

            # Spustit tool
            result = await tool.execute(context, **command.args)

            if result.success and command.tool == "file_write":
                result = self._verify_file_write(result, command=command, context=context)

            if result.success:
                self.successful_executions += 1
            else:
                self.failed_executions += 1

            return result

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.failed_executions += 1
            logger.error(f"Error executing command {command.tool}: {e}")

            return ToolResult(
                success=False,
                data=None,
                tool_name=command.tool,
                duration_ms=duration_ms,
                error=str(e),
            )

    async def _execute_mcp_tool_directly(
        self, tool_name: str, args: Dict[str, Any]
    ) -> ToolResult:
        """
        Spustí MCP tool přímo přes MCP bridge (fallback).

        Args:
            tool_name: Název nástroje
            args: Argumenty

        Returns:
            ToolResult
        """
        start_time = time.time()

        try:
            result = await self.mcp_bridge.call_mcp_tool(tool_name, args)
            duration_ms = int((time.time() - start_time) * 1000)

            if result.get("success", False):
                tool_result = ToolResult(
                    success=True,
                    data=result.get("data", result),
                    tool_name=tool_name,
                    duration_ms=duration_ms,
                )
                if tool_name == "file_write" and self._mcp_is_local():
                    return self._verify_file_write(tool_result, args=args)
                return tool_result
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    tool_name=tool_name,
                    duration_ms=duration_ms,
                    error=result.get("error", "MCP tool execution failed"),
                )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            return ToolResult(
                success=False,
                data=None,
                tool_name=tool_name,
                duration_ms=duration_ms,
                error=str(e),
            )

    def _verify_file_write(
        self,
        result: ToolResult,
        command: Optional[Command] = None,
        context: Optional[ToolExecutionContext] = None,
        args: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """Verify file writes actually landed on disk."""
        path = None
        if command:
            path = command.args.get("path")
        if not path and args:
            path = args.get("path")

        if not path:
            return result

        file_path = Path(path)
        if context and context.working_directory:
            file_path = context.working_directory / file_path

        if file_path.exists():
            result.metadata["verified_path"] = str(file_path)
            return result

        return ToolResult(
            success=False,
            data=None,
            tool_name=result.tool_name,
            duration_ms=result.duration_ms,
            error=f"File write verification failed: {file_path} not found",
        )

    def _mcp_is_local(self) -> bool:
        """Check if the MCP bridge points to a local server."""
        if not self.mcp_bridge:
            return False
        parsed = urlparse(getattr(self.mcp_bridge, "mcp_url", ""))
        host = parsed.hostname or ""
        return host in {"localhost", "127.0.0.1", "::1"}

    async def execute_with_ai_assistance(
        self, user_input: str, context: ToolExecutionContext
    ) -> Dict[str, Any]:
        """
        Spustí příkaz s AI asistencí.

        Pokud příkaz není přímý tool call, ale dotaz:
        1. AI analyzuje intent
        2. AI navrhne tools
        3. Spustí tools
        4. Pošle výsledky zpět AI
        5. AI vytvoří finální odpověď

        Příklad: "co je v tomto souboru?" → AI navrhne file_read → spustí → vrátí obsah

        Args:
            user_input: Uživatelský vstup
            context: Execution context

        Returns:
            Dict s výsledkem a AI odpovědí
        """
        logger.info(f"AI-assisted execution for: {user_input}")

        try:
            # Fáze 1: AI analyzuje intent a navrhne tools
            analysis_prompt = f"""
User request: "{user_input}"

Available tools: {list(self.tool_registry.tools.keys())}

Analyze the user's request and determine if it requires tool execution.
If yes, suggest which tools to use and with what arguments.
Respond in JSON format:
{{
    "requires_tools": true/false,
    "tools": [
        {{"name": "tool_name", "args": {{"arg": "value"}}}}
    ],
    "reasoning": "explanation"
}}
"""

            # Zavolat AI pro analýzu
            ai_response = await self.ai_client.process_request(
                analysis_prompt, files=[]
            )

            # Parse AI odpověď (jednoduché - v reálné implementaci by byl JSON parser)
            # Pro teď předpokládáme že AI vrací správný formát

            # Pokud AI navrhlo tools, spustit je
            if "requires_tools" in ai_response.get("content", ""):
                # Zde by byla logika pro extrakci tool calls z AI odpovědi
                # a jejich spuštění
                # Pro teď vrátíme základní response
                pass

            # Fáze 2: Vrátit finální odpověď
            return {
                "success": True,
                "ai_response": ai_response.get("content", ""),
                "tools_executed": [],
                "provider": ai_response.get("provider", "unknown"),
            }

        except Exception as e:
            logger.error(f"Error in AI-assisted execution: {e}")
            return {
                "success": False,
                "error": str(e),
                "ai_response": "",
                "tools_executed": [],
            }

    async def execute_workflow(
        self, workflow_name: str, context: ToolExecutionContext
    ) -> List[ToolResult]:
        """
        Spustí predefinovaný workflow (serie tool calls).

        Args:
            workflow_name: Název workflow
            context: Execution context

        Returns:
            List ToolResults z každého kroku
        """
        logger.info(f"Executing workflow: {workflow_name}")

        # Definice workflows (později můžeme načítat z JSON)
        workflows = {
            "code_review": [
                Command(tool="git_diff", args={}, raw_input="/git diff"),
                # Další kroky...
            ],
            "test_generation": [
                Command(
                    tool="file_read",
                    args={"path": "src/main.py"},
                    raw_input="/file read src/main.py",
                ),
                # Další kroky...
            ],
        }

        if workflow_name not in workflows:
            return [
                ToolResult(
                    success=False,
                    data=None,
                    tool_name="workflow",
                    duration_ms=0,
                    error=f"Workflow '{workflow_name}' not found",
                )
            ]

        workflow_commands = workflows[workflow_name]
        results = []

        for command in workflow_commands:
            result = await self.execute_command(command, context)
            results.append(result)

            # Pokud nějaký krok selže, zastavit workflow
            if not result.success:
                logger.warning(
                    f"Workflow '{workflow_name}' failed at step {len(results)}"
                )
                break

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """
        Vrátí statistiky exekuce.

        Returns:
            Dict se statistikami
        """
        success_rate = (
            (self.successful_executions / self.total_executions * 100)
            if self.total_executions > 0
            else 0.0
        )

        return {
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate": round(success_rate, 2),
        }

    async def list_available_tools(self) -> List[str]:
        """
        Vrátí seznam dostupných tools.

        Returns:
            List názvů nástrojů
        """
        return self.tool_registry.get_available_tools()

    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Vrátí informace o nástroji.

        Args:
            tool_name: Název nástroje

        Returns:
            Dict s informacemi nebo None
        """
        tool = self.tool_registry.tools.get(tool_name)
        if not tool:
            return None

        return {
            "name": tool.name,
            "category": tool.category.value,
            "availability": tool.availability.value,
            "priority": tool.priority.value,
            "capabilities": {
                "requires_network": tool.capabilities.requires_network,
                "requires_filesystem": tool.capabilities.requires_filesystem,
                "requires_auth": tool.capabilities.requires_auth,
                "max_execution_time": tool.capabilities.max_execution_time,
                "resource_intensive": tool.capabilities.resource_intensive,
            },
            "execution_count": tool.execution_count,
            "error_count": tool.error_count,
        }


# Convenience function pro rychlé použití
async def execute_command_quick(
    command_str: str,
    tool_registry: ToolRegistry,
    mcp_bridge: MCPBridge,
    working_directory: Path = Path.cwd(),
) -> ToolResult:
    """
    Convenience function pro rychlé spuštění příkazu.

    Args:
        command_str: Command string (např. "/bash ls -la")
        tool_registry: Registry nástrojů
        mcp_bridge: MCP bridge
        working_directory: Pracovní adresář

    Returns:
        ToolResult
    """
    parser = CommandParser()
    command = parser.parse(command_str)

    if not command:
        return ToolResult(
            success=False,
            data=None,
            tool_name="unknown",
            duration_ms=0,
            error=f"Could not parse command: {command_str}",
        )

    context = ToolExecutionContext(
        mode="FULL", working_directory=working_directory
    )

    # Pro quick use vytvoříme dočasný orchestrator (není optimální ale funguje)
    from .enhanced_mycoder_v2 import EnhancedMyCoderV2

    ai_client = EnhancedMyCoderV2()
    orchestrator = ToolExecutionOrchestrator(tool_registry, mcp_bridge, ai_client)

    return await orchestrator.execute_command(command, context)
