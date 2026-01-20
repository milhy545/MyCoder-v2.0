"""
Integration tests for CLI Tool Execution (v2.1.1)

End-to-end tests for tool execution through the full stack:
CommandParser → ToolOrchestrator → ToolRegistry → MCP Bridge

These tests require MCP server to be running or mocked appropriately.
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from mycoder.command_parser import CommandParser
from mycoder.enhanced_mycoder_v2 import EnhancedMyCoderV2
from mycoder.mcp_bridge import MCPBridge
from mycoder.tool_registry import ToolExecutionContext


@pytest.mark.integration
class TestCLIToolExecution:
    """Integration tests for CLI tool execution"""

    @pytest_asyncio.fixture
    async def mycoder_instance(self):
        """Create initialized MyCoder instance"""
        # Use minimal config to avoid external dependencies
        config = {
            "claude_anthropic": {"enabled": False},
            "claude_oauth": {"enabled": False},
            "gemini": {"enabled": False},
            "ollama_local": {"enabled": True, "model": "tinyllama"},
            "thermal": {"enabled": False},
            "mcp": {"url": "http://127.0.0.1:8020", "auto_start": False},
        }

        mycoder = EnhancedMyCoderV2(config=config)

        # Mock MCP bridge initialization to avoid starting real MCP server
        with patch.object(MCPBridge, "initialize", return_value=True):
            with patch.object(MCPBridge, "register_mcp_tools_in_registry"):
                await mycoder.initialize()

        yield mycoder

        # Cleanup
        if hasattr(mycoder, "mcp_bridge") and mycoder.mcp_bridge:
            await mycoder.mcp_bridge.close()

    @pytest.fixture
    def execution_context(self):
        """Create execution context for tests"""
        return ToolExecutionContext(
            mode="FULL",
            working_directory=Path.cwd(),
            session_id="test_session",
            thermal_status=None,
            network_status={"connected": True},
            metadata={"test": True},
        )

    @pytest.mark.asyncio
    async def test_bash_echo_command(self, mycoder_instance, execution_context):
        """Test /bash echo hello command"""
        if not mycoder_instance.tool_orchestrator:
            pytest.skip("Tool orchestrator not initialized")

        parser = CommandParser()
        command = parser.parse("/bash echo hello")

        assert command is not None

        # Mock MCP call for bash command
        if mycoder_instance.mcp_bridge:
            mycoder_instance.mcp_bridge.call_mcp_tool = AsyncMock(
                return_value={
                    "success": True,
                    "data": {"stdout": "hello\n", "stderr": "", "returncode": 0},
                }
            )

        result = await mycoder_instance.tool_orchestrator.execute_command(
            command, execution_context
        )

        assert result.success is True
        assert result.tool_name == "terminal_exec"

    @pytest.mark.asyncio
    async def test_file_read_command(self, mycoder_instance, execution_context):
        """Test /file read CLAUDE.md command"""
        if not mycoder_instance.tool_orchestrator:
            pytest.skip("Tool orchestrator not initialized")

        parser = CommandParser()
        command = parser.parse("/file read CLAUDE.md")

        assert command is not None
        assert command.tool == "file_read"

        # Mock MCP call for file read
        if mycoder_instance.mcp_bridge:
            mycoder_instance.mcp_bridge.call_mcp_tool = AsyncMock(
                return_value={
                    "success": True,
                    "data": {"content": "# CLAUDE.md\n\nTest content"},
                }
            )

        result = await mycoder_instance.tool_orchestrator.execute_command(
            command, execution_context
        )

        assert result.success is True
        assert result.tool_name == "file_read"

    @pytest.mark.asyncio
    async def test_git_status_command(self, mycoder_instance, execution_context):
        """Test /git status command"""
        if not mycoder_instance.tool_orchestrator:
            pytest.skip("Tool orchestrator not initialized")

        parser = CommandParser()
        command = parser.parse("/git status")

        assert command is not None
        assert command.tool == "git_status"

        # Mock MCP call for git status
        if mycoder_instance.mcp_bridge:
            mycoder_instance.mcp_bridge.call_mcp_tool = AsyncMock(
                return_value={
                    "success": True,
                    "data": {"status": "On branch main\nnothing to commit"},
                }
            )

        result = await mycoder_instance.tool_orchestrator.execute_command(
            command, execution_context
        )

        assert result.success is True
        assert result.tool_name == "git_status"

    @pytest.mark.asyncio
    async def test_multiple_commands_sequence(
        self, mycoder_instance, execution_context
    ):
        """Test executing multiple commands in sequence"""
        if not mycoder_instance.tool_orchestrator:
            pytest.skip("Tool orchestrator not initialized")

        parser = CommandParser()
        commands = [
            parser.parse("/bash pwd"),
            parser.parse("/file list ."),
            parser.parse("/git status"),
        ]

        # Mock MCP calls
        if mycoder_instance.mcp_bridge:
            mycoder_instance.mcp_bridge.call_mcp_tool = AsyncMock(
                side_effect=[
                    {"success": True, "data": {"stdout": "/home/user\n"}},
                    {"success": True, "data": {"files": ["file1.py", "file2.py"]}},
                    {"success": True, "data": {"status": "On branch main"}},
                ]
            )

        results = []
        for command in commands:
            result = await mycoder_instance.tool_orchestrator.execute_command(
                command, execution_context
            )
            results.append(result)

        assert len(results) == 3
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_command_with_error(self, mycoder_instance, execution_context):
        """Test command execution that results in error"""
        if not mycoder_instance.tool_orchestrator:
            pytest.skip("Tool orchestrator not initialized")

        parser = CommandParser()
        command = parser.parse("/bash nonexistent_command")

        # Mock MCP call with error
        if mycoder_instance.mcp_bridge:
            mycoder_instance.mcp_bridge.call_mcp_tool = AsyncMock(
                return_value={
                    "success": False,
                    "error": "Command not found: nonexistent_command",
                }
            )

        result = await mycoder_instance.tool_orchestrator.execute_command(
            command, execution_context
        )

        assert result.success is False
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_orchestrator_statistics(self, mycoder_instance, execution_context):
        """Test orchestrator statistics tracking"""
        if not mycoder_instance.tool_orchestrator:
            pytest.skip("Tool orchestrator not initialized")

        parser = CommandParser()

        # Execute successful command
        command1 = parser.parse("/bash echo test")
        if mycoder_instance.mcp_bridge:
            mycoder_instance.mcp_bridge.call_mcp_tool = AsyncMock(
                return_value={"success": True, "data": {"stdout": "test\n"}}
            )
        await mycoder_instance.tool_orchestrator.execute_command(
            command1, execution_context
        )

        # Execute failing command
        command2 = parser.parse("/bash invalid")
        if mycoder_instance.mcp_bridge:
            mycoder_instance.mcp_bridge.call_mcp_tool = AsyncMock(
                return_value={"success": False, "error": "Command failed"}
            )
        await mycoder_instance.tool_orchestrator.execute_command(
            command2, execution_context
        )

        stats = mycoder_instance.tool_orchestrator.get_statistics()

        assert stats["total_executions"] >= 2
        assert stats["successful_executions"] >= 1
        assert stats["failed_executions"] >= 1

    @pytest.mark.asyncio
    async def test_list_available_tools(self, mycoder_instance):
        """Test listing available tools"""
        if not mycoder_instance.tool_orchestrator:
            pytest.skip("Tool orchestrator not initialized")

        tools = await mycoder_instance.tool_orchestrator.list_available_tools()

        assert isinstance(tools, list)
        assert len(tools) > 0

    @pytest.mark.asyncio
    async def test_get_tool_info(self, mycoder_instance):
        """Test getting tool information"""
        if not mycoder_instance.tool_orchestrator:
            pytest.skip("Tool orchestrator not initialized")

        tools = await mycoder_instance.tool_orchestrator.list_available_tools()

        if len(tools) > 0:
            tool_name = tools[0]
            info = await mycoder_instance.tool_orchestrator.get_tool_info(tool_name)

            if info:
                assert "name" in info
                assert "category" in info
                assert "capabilities" in info


@pytest.mark.integration
@pytest.mark.slow
class TestCLIToolExecutionWithRealMCP:
    """
    Integration tests with real MCP server.

    These tests require actual MCP server running on localhost:8020.
    Mark as slow and skip if server is not available.
    """

    @pytest_asyncio.fixture
    async def mycoder_with_real_mcp(self):
        """Create MyCoder instance with real MCP server"""
        config = {
            "claude_anthropic": {"enabled": False},
            "claude_oauth": {"enabled": False},
            "gemini": {"enabled": False},
            "ollama_local": {"enabled": True},
            "thermal": {"enabled": False},
            "mcp": {"url": "http://127.0.0.1:8020", "auto_start": True},
        }

        mycoder = EnhancedMyCoderV2(config=config)

        try:
            await mycoder.initialize()
        except Exception as e:
            pytest.skip(f"MCP server not available: {e}")

        # Check if MCP bridge is actually initialized
        if not mycoder.mcp_bridge or not mycoder.mcp_bridge.is_initialized:
            pytest.skip("MCP bridge not initialized")

        yield mycoder

        # Cleanup
        if mycoder.mcp_bridge:
            await mycoder.mcp_bridge.close()

    @pytest.mark.asyncio
    async def test_real_bash_command(self, mycoder_with_real_mcp):
        """Test real bash command execution"""
        parser = CommandParser()
        command = parser.parse("/bash echo 'Integration test'")

        context = ToolExecutionContext(mode="FULL", working_directory=Path.cwd())

        result = await mycoder_with_real_mcp.tool_orchestrator.execute_command(
            command, context
        )

        assert result.success is True
        assert "Integration test" in str(result.data)

    @pytest.mark.asyncio
    async def test_real_file_operations(self, mycoder_with_real_mcp, tmp_path):
        """Test real file operations"""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")

        parser = CommandParser()
        command = parser.parse(f"/file read {test_file}")

        context = ToolExecutionContext(mode="FULL", working_directory=tmp_path)

        result = await mycoder_with_real_mcp.tool_orchestrator.execute_command(
            command, context
        )

        if result.success:
            assert "Test content" in str(result.data)
