"""
Unit tests for MCPBridge (v2.1.1)

Tests MCP bridge functionality for connecting tool_registry with MCP server.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from mycoder.mcp_bridge import MCPBridge, MCPToolWrapper
from mycoder.tool_registry import (
    ToolCategory,
    ToolExecutionContext,
    ToolResult,
    ToolRegistry,
)


class TestMCPBridge:
    """Test suite for MCPBridge"""

    @pytest.fixture
    def mcp_bridge(self):
        """Create MCPBridge instance for testing"""
        bridge = MCPBridge(
            mcp_url="http://127.0.0.1:8020",
            auto_start=False,  # Don't auto-start in tests
        )
        return bridge

    @pytest.fixture
    def tool_registry(self):
        """Create ToolRegistry instance for testing"""
        from mycoder.tool_registry import ToolRegistry

        return ToolRegistry()

    def test_mcp_bridge_initialization(self, mcp_bridge):
        """Test MCPBridge initialization"""
        assert mcp_bridge.mcp_url == "http://127.0.0.1:8020"
        assert mcp_bridge.auto_start == False
        assert mcp_bridge.is_initialized == False
        assert mcp_bridge.mcp_tools == {}

    @pytest.mark.asyncio
    async def test_check_mcp_health_no_session(self, mcp_bridge):
        """Test health check without session"""
        result = await mcp_bridge._check_mcp_health()
        assert result == False

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_check_mcp_health_success(self, mock_session_class, mcp_bridge):
        """Test successful health check"""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        # Mock session
        mock_session = AsyncMock()
        mock_session.get = Mock(return_value=mock_response)
        mcp_bridge.session = mock_session

        result = await mcp_bridge._check_mcp_health()
        assert result == True

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_check_mcp_health_failure(self, mock_session_class, mcp_bridge):
        """Test failed health check"""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        # Mock session
        mock_session = AsyncMock()
        mock_session.get = Mock(return_value=mock_response)
        mcp_bridge.session = mock_session

        result = await mcp_bridge._check_mcp_health()
        assert result == False

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_call_mcp_tool_success(self, mock_session_class, mcp_bridge):
        """Test successful MCP tool call"""
        # Mock response
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(
            return_value={"success": True, "data": {"stdout": "hello"}}
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        # Mock session
        mock_session = AsyncMock()
        mock_session.post = Mock(return_value=mock_response)
        mcp_bridge.session = mock_session

        result = await mcp_bridge.call_mcp_tool("terminal_exec", {"command": "echo hello"})

        assert result["success"] == True
        assert "data" in result

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession")
    async def test_call_mcp_tool_error(self, mock_session_class, mcp_bridge):
        """Test MCP tool call with error"""
        # Mock response
        mock_response = AsyncMock()
        mock_response.json = AsyncMock(
            return_value={"success": False, "error": "Tool not found"}
        )
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        # Mock session
        mock_session = AsyncMock()
        mock_session.post = Mock(return_value=mock_response)
        mcp_bridge.session = mock_session

        result = await mcp_bridge.call_mcp_tool("invalid_tool", {})

        assert result["success"] == False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_call_mcp_tool_no_session(self, mcp_bridge):
        """Test MCP tool call without session"""
        result = await mcp_bridge.call_mcp_tool("terminal_exec", {"command": "ls"})

        assert result["success"] == False
        assert "error" in result

    def test_create_mcp_tool_wrapper_file_operations(self, mcp_bridge):
        """Test creating MCP tool wrapper for file operations"""
        wrapper = mcp_bridge._create_mcp_tool_wrapper(
            "file_read", {"service": "filesystem", "name": "file_read"}
        )

        assert isinstance(wrapper, MCPToolWrapper)
        assert wrapper.name == "file_read"
        assert wrapper.category == ToolCategory.FILE_OPERATIONS

    def test_create_mcp_tool_wrapper_terminal_operations(self, mcp_bridge):
        """Test creating MCP tool wrapper for terminal operations"""
        wrapper = mcp_bridge._create_mcp_tool_wrapper(
            "terminal_exec", {"service": "shell", "name": "terminal_exec"}
        )

        assert isinstance(wrapper, MCPToolWrapper)
        assert wrapper.name == "terminal_exec"
        assert wrapper.category == ToolCategory.TERMINAL_OPERATIONS

    def test_create_mcp_tool_wrapper_git_operations(self, mcp_bridge):
        """Test creating MCP tool wrapper for git operations"""
        wrapper = mcp_bridge._create_mcp_tool_wrapper(
            "git_status", {"service": "git", "name": "git_status"}
        )

        assert isinstance(wrapper, MCPToolWrapper)
        assert wrapper.name == "git_status"
        assert wrapper.category == ToolCategory.GIT_OPERATIONS

    def test_create_mcp_tool_wrapper_memory_operations(self, mcp_bridge):
        """Test creating MCP tool wrapper for memory operations"""
        wrapper = mcp_bridge._create_mcp_tool_wrapper(
            "store_memory", {"service": "memory", "name": "store_memory"}
        )

        assert isinstance(wrapper, MCPToolWrapper)
        assert wrapper.name == "store_memory"
        assert wrapper.category == ToolCategory.MEMORY_OPERATIONS

    @pytest.mark.asyncio
    async def test_close(self, mcp_bridge):
        """Test closing MCP bridge"""
        # Create mock session
        mock_session = AsyncMock()
        mock_session.close = AsyncMock()
        mcp_bridge.session = mock_session
        mcp_bridge.is_initialized = True

        await mcp_bridge.close()

        assert mcp_bridge.session is None
        assert mcp_bridge.is_initialized == False


class TestMCPToolWrapper:
    """Test suite for MCPToolWrapper"""

    @pytest.fixture
    def mcp_bridge_mock(self):
        """Create mock MCPBridge"""
        bridge = Mock(spec=MCPBridge)
        bridge.call_mcp_tool = AsyncMock()
        return bridge

    @pytest.fixture
    def tool_wrapper(self, mcp_bridge_mock):
        """Create MCPToolWrapper instance"""
        return MCPToolWrapper(
            name="test_tool",
            category=ToolCategory.FILE_OPERATIONS,
            mcp_bridge=mcp_bridge_mock,
            tool_info={"service": "test", "name": "test_tool"},
        )

    def test_mcp_tool_wrapper_initialization(self, tool_wrapper, mcp_bridge_mock):
        """Test MCPToolWrapper initialization"""
        assert tool_wrapper.name == "test_tool"
        assert tool_wrapper.category == ToolCategory.FILE_OPERATIONS
        assert tool_wrapper.mcp_bridge == mcp_bridge_mock

    @pytest.mark.asyncio
    async def test_execute_success(self, tool_wrapper, mcp_bridge_mock):
        """Test successful tool execution"""
        # Mock successful MCP call
        mcp_bridge_mock.call_mcp_tool.return_value = {
            "success": True,
            "data": {"result": "success"},
        }

        context = ToolExecutionContext(mode="FULL")
        result = await tool_wrapper.execute(context, arg1="value1")

        assert isinstance(result, ToolResult)
        assert result.success == True
        assert result.tool_name == "test_tool"
        assert result.data == {"result": "success"}

    @pytest.mark.asyncio
    async def test_execute_failure(self, tool_wrapper, mcp_bridge_mock):
        """Test failed tool execution"""
        # Mock failed MCP call
        mcp_bridge_mock.call_mcp_tool.return_value = {
            "success": False,
            "error": "Tool execution failed",
        }

        context = ToolExecutionContext(mode="FULL")
        result = await tool_wrapper.execute(context)

        assert isinstance(result, ToolResult)
        assert result.success == False
        assert result.tool_name == "test_tool"
        assert "Tool execution failed" in result.error

    @pytest.mark.asyncio
    async def test_execute_exception(self, tool_wrapper, mcp_bridge_mock):
        """Test tool execution with exception"""
        # Mock exception
        mcp_bridge_mock.call_mcp_tool.side_effect = Exception("Connection error")

        context = ToolExecutionContext(mode="FULL")
        result = await tool_wrapper.execute(context)

        assert isinstance(result, ToolResult)
        assert result.success == False
        assert "Connection error" in result.error

    @pytest.mark.asyncio
    async def test_validate_context(self, tool_wrapper):
        """Test context validation"""
        context = ToolExecutionContext(mode="FULL")
        result = await tool_wrapper.validate_context(context)

        # MCP tools are always available
        assert result == True
