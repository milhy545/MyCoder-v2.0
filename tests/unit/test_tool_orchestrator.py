"""
Unit tests for ToolExecutionOrchestrator (v2.1.1)

Tests orchestration of tool execution between CLI, tool_registry, and MCP.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from mycoder.command_parser import Command
from mycoder.mcp_bridge import MCPBridge
from mycoder.tool_orchestrator import (
    ToolExecutionOrchestrator,
    execute_command_quick,
)
from mycoder.tool_registry import (
    BaseTool,
    ToolAvailability,
    ToolCapabilities,
    ToolCategory,
    ToolExecutionContext,
    ToolPriority,
    ToolRegistry,
    ToolResult,
)


class MockTool(BaseTool):
    """Mock tool for testing"""

    def __init__(self, name="mock_tool", should_succeed=True):
        super().__init__(
            name=name,
            category=ToolCategory.FILE_OPERATIONS,
            availability=ToolAvailability.ALWAYS,
            priority=ToolPriority.NORMAL,
            capabilities=ToolCapabilities(),
        )
        self.should_succeed = should_succeed
        self.execute_called = False
        self.validate_called = False

    async def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """Mock execute"""
        self.execute_called = True
        if self.should_succeed:
            return ToolResult(
                success=True,
                data={"result": "success"},
                tool_name=self.name,
                duration_ms=10,
            )
        else:
            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                duration_ms=10,
                error="Mock execution failed",
            )

    async def validate_context(self, context: ToolExecutionContext) -> bool:
        """Mock validate"""
        self.validate_called = True
        return True


class TestToolExecutionOrchestrator:
    """Test suite for ToolExecutionOrchestrator"""

    @pytest.fixture
    def tool_registry(self):
        """Create ToolRegistry with mock tools"""
        registry = ToolRegistry()
        # Register mock tools
        registry.register_tool(MockTool(name="test_tool", should_succeed=True))
        registry.register_tool(MockTool(name="failing_tool", should_succeed=False))
        return registry

    @pytest.fixture
    def mcp_bridge_mock(self):
        """Create mock MCPBridge"""
        bridge = Mock(spec=MCPBridge)
        bridge.call_mcp_tool = AsyncMock(
            return_value={"success": True, "data": {"result": "mcp_success"}}
        )
        return bridge

    @pytest.fixture
    def ai_client_mock(self):
        """Create mock AI client"""
        client = Mock()
        client.process_request = AsyncMock(
            return_value={"content": "AI response", "provider": "test"}
        )
        return client

    @pytest.fixture
    def orchestrator(self, tool_registry, mcp_bridge_mock, ai_client_mock):
        """Create ToolExecutionOrchestrator"""
        return ToolExecutionOrchestrator(
            tool_registry=tool_registry,
            mcp_bridge=mcp_bridge_mock,
            ai_client=ai_client_mock,
        )

    @pytest.fixture
    def execution_context(self):
        """Create execution context"""
        return ToolExecutionContext(
            mode="FULL",
            working_directory=Path.cwd(),
        )

    def test_orchestrator_initialization(
        self, orchestrator, tool_registry, mcp_bridge_mock, ai_client_mock
    ):
        """Test orchestrator initialization"""
        assert orchestrator.tool_registry == tool_registry
        assert orchestrator.mcp_bridge == mcp_bridge_mock
        assert orchestrator.ai_client == ai_client_mock
        assert orchestrator.total_executions == 0
        assert orchestrator.successful_executions == 0
        assert orchestrator.failed_executions == 0

    @pytest.mark.asyncio
    async def test_execute_command_success(self, orchestrator, execution_context):
        """Test successful command execution"""
        command = Command(
            tool="test_tool",
            args={"arg1": "value1"},
            raw_input="/test_tool arg1=value1",
        )

        result = await orchestrator.execute_command(command, execution_context)

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.tool_name == "test_tool"
        assert orchestrator.total_executions == 1
        assert orchestrator.successful_executions == 1

    @pytest.mark.asyncio
    async def test_execute_command_failure(self, orchestrator, execution_context):
        """Test failed command execution"""
        command = Command(tool="failing_tool", args={}, raw_input="/failing_tool")

        result = await orchestrator.execute_command(command, execution_context)

        assert isinstance(result, ToolResult)
        assert result.success is False
        assert "Mock execution failed" in result.error
        assert orchestrator.total_executions == 1
        assert orchestrator.failed_executions == 1

    @pytest.mark.asyncio
    async def test_execute_command_tool_not_found(
        self, orchestrator, execution_context, mcp_bridge_mock
    ):
        """Test command execution with tool not in registry (fallback to MCP)"""
        command = Command(
            tool="mcp_only_tool", args={"arg": "value"}, raw_input="/mcp_only_tool"
        )

        result = await orchestrator.execute_command(command, execution_context)

        assert isinstance(result, ToolResult)
        assert result.success is True  # Mock MCP returns success
        assert orchestrator.total_executions == 1
        # Should have called MCP bridge
        mcp_bridge_mock.call_mcp_tool.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_command_exception(self, orchestrator, execution_context):
        """Test command execution with exception"""
        command = Command(tool="nonexistent_tool", args={}, raw_input="/nonexistent")

        # Mock MCP bridge to raise exception
        orchestrator.mcp_bridge.call_mcp_tool = AsyncMock(
            side_effect=Exception("Connection error")
        )

        result = await orchestrator.execute_command(command, execution_context)

        assert isinstance(result, ToolResult)
        assert result.success is False
        assert "Connection error" in result.error
        assert orchestrator.failed_executions == 1

    @pytest.mark.asyncio
    async def test_execute_mcp_tool_directly_success(
        self, orchestrator, mcp_bridge_mock
    ):
        """Test direct MCP tool execution (success)"""
        result = await orchestrator._execute_mcp_tool_directly(
            "mcp_tool", {"arg": "value"}
        )

        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.tool_name == "mcp_tool"
        mcp_bridge_mock.call_mcp_tool.assert_called_once_with(
            "mcp_tool", {"arg": "value"}
        )

    @pytest.mark.asyncio
    async def test_execute_mcp_tool_directly_failure(
        self, orchestrator, mcp_bridge_mock
    ):
        """Test direct MCP tool execution (failure)"""
        mcp_bridge_mock.call_mcp_tool.return_value = {
            "success": False,
            "error": "MCP tool failed",
        }

        result = await orchestrator._execute_mcp_tool_directly("mcp_tool", {})

        assert isinstance(result, ToolResult)
        assert result.success is False
        assert "MCP tool failed" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_ai_assistance(self, orchestrator, execution_context):
        """Test AI-assisted execution"""
        result = await orchestrator.execute_with_ai_assistance(
            "what is in this file?", execution_context
        )

        assert isinstance(result, dict)
        assert result["success"] is True
        assert "ai_response" in result
        assert "tools_executed" in result

    @pytest.mark.asyncio
    async def test_execute_workflow_success(self, orchestrator, execution_context):
        """Test workflow execution (not fully implemented, basic test)"""
        results = await orchestrator.execute_workflow(
            "test_workflow", execution_context
        )

        assert isinstance(results, list)
        # Workflow not found returns error result
        assert len(results) == 1
        assert results[0].success is False

    def test_get_statistics_no_executions(self, orchestrator):
        """Test getting statistics with no executions"""
        stats = orchestrator.get_statistics()

        assert stats["total_executions"] == 0
        assert stats["successful_executions"] == 0
        assert stats["failed_executions"] == 0
        assert stats["success_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_get_statistics_with_executions(
        self, orchestrator, execution_context
    ):
        """Test getting statistics after executions"""
        # Execute successful command
        command1 = Command(tool="test_tool", args={}, raw_input="/test_tool")
        await orchestrator.execute_command(command1, execution_context)

        # Execute failing command
        command2 = Command(tool="failing_tool", args={}, raw_input="/failing_tool")
        await orchestrator.execute_command(command2, execution_context)

        stats = orchestrator.get_statistics()

        assert stats["total_executions"] == 2
        assert stats["successful_executions"] == 1
        assert stats["failed_executions"] == 1
        assert stats["success_rate"] == 50.0

    @pytest.mark.asyncio
    async def test_list_available_tools(self, orchestrator):
        """Test listing available tools"""
        tools = await orchestrator.list_available_tools()

        assert isinstance(tools, list)
        assert "test_tool" in tools
        assert "failing_tool" in tools

    @pytest.mark.asyncio
    async def test_get_tool_info_existing(self, orchestrator):
        """Test getting info for existing tool"""
        info = await orchestrator.get_tool_info("test_tool")

        assert isinstance(info, dict)
        assert info["name"] == "test_tool"
        assert info["category"] == "file_operations"
        assert "capabilities" in info

    @pytest.mark.asyncio
    async def test_get_tool_info_nonexistent(self, orchestrator):
        """Test getting info for nonexistent tool"""
        info = await orchestrator.get_tool_info("nonexistent")

        assert info is None


class TestExecuteCommandQuick:
    """Test suite for execute_command_quick convenience function"""

    @pytest.mark.asyncio
    async def test_execute_command_quick_invalid_command(self):
        """Test quick execution with invalid command"""
        # Create mocks
        mock_registry = Mock(spec=ToolRegistry)
        mock_bridge = Mock(spec=MCPBridge)

        result = await execute_command_quick(
            "invalid command", mock_registry, mock_bridge
        )

        assert isinstance(result, ToolResult)
        assert result.success is False
        assert "Could not parse command" in result.error

    @pytest.mark.skip(
        reason="Complex integration with EnhancedMyCoderV2, tested in integration tests"
    )
    @pytest.mark.asyncio
    async def test_execute_command_quick_valid_command(self):
        """Test quick execution with valid command"""
        # This test requires complex mocking of EnhancedMyCoderV2
        # Better tested in integration tests
        pass
