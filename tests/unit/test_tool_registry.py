"""
Comprehensive Unit Tests for Tool Registry System

Tests the FEI-inspired tool registry with all tool categories,
execution contexts, and thermal-aware operations.
"""

import asyncio
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mycoder.tool_registry import (
    BaseTool,
    FileOperationTool,
    MCPTool,
    ThermalAwareTool,
    ToolAvailability,
    ToolCapabilities,
    ToolCategory,
    ToolExecutionContext,
    ToolPriority,
    ToolRegistry,
    ToolResult,
    get_tool_registry,
)


class TestToolCapabilities:
    """Test ToolCapabilities data structure"""

    def test_capabilities_default(self):
        """Test default capabilities"""
        capabilities = ToolCapabilities()

        assert capabilities.requires_network is False
        assert capabilities.requires_filesystem is False
        assert capabilities.requires_auth is False
        assert capabilities.requires_mcp is False
        assert capabilities.requires_thermal_safe is False
        assert capabilities.max_execution_time == 30
        assert capabilities.resource_intensive is False
        assert capabilities.supports_streaming is False
        assert capabilities.supports_caching is False

    def test_capabilities_custom(self):
        """Test custom capabilities"""
        capabilities = ToolCapabilities(
            requires_network=True,
            requires_filesystem=True,
            max_execution_time=120,
            resource_intensive=True,
            supports_streaming=True,
        )

        assert capabilities.requires_network is True
        assert capabilities.requires_filesystem is True
        assert capabilities.max_execution_time == 120
        assert capabilities.resource_intensive is True
        assert capabilities.supports_streaming is True


class TestToolExecutionContext:
    """Test ToolExecutionContext data structure"""

    def test_context_creation(self):
        """Test context creation with all parameters"""
        working_dir = Path("/tmp/test")
        thermal_status = {"cpu_temp": 65, "safe_operation": True}

        context = ToolExecutionContext(
            mode="FULL",
            working_directory=working_dir,
            user_id="test_user",
            session_id="test_session",
            thermal_status=thermal_status,
            metadata={"test": "value"},
        )

        assert context.mode == "FULL"
        assert context.working_directory == working_dir
        assert context.user_id == "test_user"
        assert context.session_id == "test_session"
        assert context.thermal_status == thermal_status
        assert context.metadata["test"] == "value"

    def test_context_defaults(self):
        """Test context with default values"""
        context = ToolExecutionContext(mode="RECOVERY")

        assert context.mode == "RECOVERY"
        assert context.working_directory is None
        assert context.user_id is None
        assert context.session_id is None
        assert context.thermal_status is None
        assert context.network_status is None
        assert context.resource_limits is None
        assert context.metadata == {}


class TestToolResult:
    """Test ToolResult data structure"""

    def test_result_success(self):
        """Test successful tool result"""
        result = ToolResult(
            success=True,
            data={"file_content": "Hello World"},
            tool_name="file_read",
            duration_ms=1500,
            metadata={"file_path": "/test.txt"},
        )

        assert result.success is True
        assert result.data["file_content"] == "Hello World"
        assert result.tool_name == "file_read"
        assert result.duration_ms == 1500
        assert result.error is None
        assert result.warnings == []
        assert result.metadata["file_path"] == "/test.txt"

    def test_result_failure(self):
        """Test failed tool result"""
        result = ToolResult(
            success=False,
            data=None,
            tool_name="file_write",
            duration_ms=500,
            error="File not found",
            warnings=["Permission issue"],
        )

        assert result.success is False
        assert result.data is None
        assert result.error == "File not found"
        assert result.warnings == ["Permission issue"]
        assert result.metadata == {}


class TestBaseTool:
    """Test BaseTool abstract base class"""

    def create_test_tool(self, name="test_tool", availability=ToolAvailability.ALWAYS):
        """Create a test tool implementation"""

        class TestTool(BaseTool):
            async def execute(self, context, **kwargs):
                return ToolResult(
                    success=True,
                    data="test_result",
                    tool_name=self.name,
                    duration_ms=100,
                )

            async def validate_context(self, context):
                return True

        capabilities = ToolCapabilities(max_execution_time=60)
        return TestTool(
            name=name,
            category=ToolCategory.FILE_OPERATIONS,
            availability=availability,
            priority=ToolPriority.NORMAL,
            capabilities=capabilities,
        )

    def test_tool_initialization(self):
        """Test tool initialization"""
        tool = self.create_test_tool()

        assert tool.name == "test_tool"
        assert tool.category == ToolCategory.FILE_OPERATIONS
        assert tool.availability == ToolAvailability.ALWAYS
        assert tool.priority == ToolPriority.NORMAL
        assert tool.execution_count == 0
        assert tool.error_count == 0
        assert tool.total_execution_time == 0
        assert tool.last_execution == 0

    def test_can_execute_in_mode_full(self):
        """Test mode availability for FULL mode"""
        # Test tool available in all modes
        tool_always = self.create_test_tool(availability=ToolAvailability.ALWAYS)
        assert tool_always.can_execute_in_mode("FULL") is True

        # Test tool only in FULL mode
        tool_full_only = self.create_test_tool(availability=ToolAvailability.FULL_ONLY)
        assert tool_full_only.can_execute_in_mode("FULL") is True

        # Test tool in DEGRADED+ modes
        tool_degraded_plus = self.create_test_tool(
            availability=ToolAvailability.DEGRADED_PLUS
        )
        assert tool_degraded_plus.can_execute_in_mode("FULL") is True

    def test_can_execute_in_mode_recovery(self):
        """Test mode availability for RECOVERY mode"""
        # Test tool available in all modes
        tool_always = self.create_test_tool(availability=ToolAvailability.ALWAYS)
        assert tool_always.can_execute_in_mode("RECOVERY") is True

        # Test tool only in FULL mode
        tool_full_only = self.create_test_tool(availability=ToolAvailability.FULL_ONLY)
        assert tool_full_only.can_execute_in_mode("RECOVERY") is False

        # Test local-only tools
        tool_local_only = self.create_test_tool(
            availability=ToolAvailability.LOCAL_ONLY
        )
        assert tool_local_only.can_execute_in_mode("RECOVERY") is True

        # Test recovery-only tools
        tool_recovery_only = self.create_test_tool(
            availability=ToolAvailability.RECOVERY_ONLY
        )
        assert tool_recovery_only.can_execute_in_mode("RECOVERY") is True

    def test_get_metrics(self):
        """Test metrics collection"""
        tool = self.create_test_tool()
        tool.execution_count = 10
        tool.error_count = 2
        tool.total_execution_time = 15000
        tool.last_execution = time.time()

        metrics = tool.get_metrics()

        assert metrics["name"] == "test_tool"
        assert metrics["category"] == "file_operations"
        assert metrics["execution_count"] == 10
        assert metrics["error_count"] == 2
        assert metrics["success_rate"] == 0.8
        assert metrics["avg_execution_time"] == 1500.0
        assert metrics["last_execution"] > 0


class TestFileOperationTool:
    """Test FileOperationTool implementation"""

    def create_tool(self):
        """Create file operation tool"""
        return FileOperationTool("file_ops")

    def test_tool_initialization(self):
        """Test file operation tool initialization"""
        tool = self.create_tool()

        assert tool.name == "file_ops"
        assert tool.category == ToolCategory.FILE_OPERATIONS
        assert tool.availability == ToolAvailability.ALWAYS
        assert tool.priority == ToolPriority.HIGH
        assert tool.capabilities.requires_filesystem is True
        assert tool.capabilities.supports_caching is True

    @pytest.mark.asyncio
    async def test_validate_context_with_working_directory(self):
        """Test context validation with working directory"""
        tool = self.create_tool()

        with TemporaryDirectory() as temp_dir:
            context = ToolExecutionContext(
                mode="FULL", working_directory=Path(temp_dir)
            )

            is_valid = await tool.validate_context(context)
            assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_context_without_working_directory(self):
        """Test context validation without working directory"""
        tool = self.create_tool()
        context = ToolExecutionContext(mode="FULL")

        is_valid = await tool.validate_context(context)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_execute_read_operation(self):
        """Test file read operation"""
        tool = self.create_tool()

        with TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = Path(temp_dir) / "test.txt"
            test_content = "Hello, World!"
            test_file.write_text(test_content)

            context = ToolExecutionContext(
                mode="FULL", working_directory=Path(temp_dir)
            )

            result = await tool.execute(context, operation="read", path="test.txt")

            assert result.success is True
            assert result.data == test_content
            assert result.tool_name == "file_ops"
            assert result.metadata["operation"] == "read"
            assert "test.txt" in str(result.metadata["path"])

    @pytest.mark.asyncio
    async def test_execute_write_operation(self):
        """Test file write operation"""
        tool = self.create_tool()

        with TemporaryDirectory() as temp_dir:
            context = ToolExecutionContext(
                mode="FULL", working_directory=Path(temp_dir)
            )

            test_content = "Hello from MyCoder!"
            result = await tool.execute(
                context, operation="write", path="output.txt", content=test_content
            )

            assert result.success is True
            assert "Written" in result.data
            assert result.metadata["operation"] == "write"

            # Verify file was actually written
            written_file = Path(temp_dir) / "output.txt"
            assert written_file.exists()
            assert written_file.read_text() == test_content

    @pytest.mark.asyncio
    async def test_execute_list_operation(self):
        """Test directory listing operation"""
        tool = self.create_tool()

        with TemporaryDirectory() as temp_dir:
            # Create test files
            (Path(temp_dir) / "file1.txt").write_text("content1")
            (Path(temp_dir) / "file2.py").write_text("content2")
            (Path(temp_dir) / "subdir").mkdir()

            context = ToolExecutionContext(
                mode="FULL", working_directory=Path(temp_dir)
            )

            result = await tool.execute(context, operation="list", path=".")

            assert result.success is True
            assert isinstance(result.data, list)
            assert len(result.data) == 3

            # Check that all created items are listed
            listed_names = [Path(item).name for item in result.data]
            assert "file1.txt" in listed_names
            assert "file2.py" in listed_names
            assert "subdir" in listed_names

    @pytest.mark.asyncio
    async def test_execute_exists_operation(self):
        """Test file existence check"""
        tool = self.create_tool()

        with TemporaryDirectory() as temp_dir:
            # Create test file
            test_file = Path(temp_dir) / "exists.txt"
            test_file.write_text("I exist")

            context = ToolExecutionContext(
                mode="FULL", working_directory=Path(temp_dir)
            )

            # Test existing file
            result = await tool.execute(context, operation="exists", path="exists.txt")

            assert result.success is True
            assert result.data is True

            # Test non-existing file
            result = await tool.execute(
                context, operation="exists", path="nonexistent.txt"
            )

            assert result.success is True
            assert result.data is False

    @pytest.mark.asyncio
    async def test_execute_invalid_operation(self):
        """Test invalid operation handling"""
        tool = self.create_tool()

        with TemporaryDirectory() as temp_dir:
            context = ToolExecutionContext(
                mode="FULL", working_directory=Path(temp_dir)
            )

            result = await tool.execute(context, operation="invalid_op")

            assert result.success is False
            assert "Unsupported operation" in result.error

    @pytest.mark.asyncio
    async def test_execute_file_not_found(self):
        """Test file not found error handling"""
        tool = self.create_tool()

        with TemporaryDirectory() as temp_dir:
            context = ToolExecutionContext(
                mode="FULL", working_directory=Path(temp_dir)
            )

            result = await tool.execute(
                context, operation="read", path="nonexistent.txt"
            )

            assert result.success is False
            assert "File not found" in result.error

    @pytest.mark.asyncio
    async def test_execute_missing_path(self):
        """Test missing path parameter"""
        tool = self.create_tool()

        with TemporaryDirectory() as temp_dir:
            context = ToolExecutionContext(
                mode="FULL", working_directory=Path(temp_dir)
            )

            result = await tool.execute(context, operation="read")

            assert result.success is False
            assert "File path is required" in result.error

    @pytest.mark.asyncio
    async def test_execute_write_missing_content(self):
        """Test write operation without content"""
        tool = self.create_tool()

        with TemporaryDirectory() as temp_dir:
            context = ToolExecutionContext(
                mode="FULL", working_directory=Path(temp_dir)
            )

            result = await tool.execute(context, operation="write", path="test.txt")

            assert result.success is False
            assert "Content is required" in result.error


class TestMCPTool:
    """Test MCPTool implementation"""

    def create_tool(self):
        """Create MCP tool"""
        return MCPTool("test_mcp", "git_execute")

    def test_tool_initialization(self):
        """Test MCP tool initialization"""
        tool = self.create_tool()

        assert tool.name == "test_mcp"
        assert tool.category == ToolCategory.RESEARCH_OPERATIONS
        assert tool.availability == ToolAvailability.FULL_ONLY
        assert tool.priority == ToolPriority.NORMAL
        assert tool.capabilities.requires_network is True
        assert tool.capabilities.requires_mcp is True
        assert tool.capabilities.resource_intensive is True
        assert tool.mcp_tool_name == "git_execute"

    @pytest.mark.asyncio
    async def test_validate_context_with_network(self):
        """Test context validation with network status"""
        tool = self.create_tool()

        context = ToolExecutionContext(
            mode="FULL", network_status={"connected": True, "quality": "good"}
        )

        is_valid = await tool.validate_context(context)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_context_without_network(self):
        """Test context validation without network"""
        tool = self.create_tool()

        context = ToolExecutionContext(mode="FULL", network_status={"connected": False})

        is_valid = await tool.validate_context(context)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_context_no_network_status(self):
        """Test context validation with no network status"""
        tool = self.create_tool()
        context = ToolExecutionContext(mode="FULL")

        is_valid = await tool.validate_context(context)
        assert is_valid is True  # Assumes network available if no status

    @pytest.mark.asyncio
    @patch("mycoder.tool_registry.MCPConnector")
    async def test_execute_success(self, mock_mcp_connector_class):
        """Test successful MCP tool execution"""
        # Mock MCP connector
        mock_connector = AsyncMock()
        mock_connector.is_orchestrator_available.return_value = True
        mock_connector.execute_tool.return_value = {
            "success": True,
            "result": {"status": "completed", "output": "Git operation successful"},
        }
        mock_mcp_connector_class.return_value = mock_connector

        tool = self.create_tool()
        context = ToolExecutionContext(mode="FULL")

        result = await tool.execute(
            context, command="git status", repo_path="/test/repo"
        )

        assert result.success is True
        assert result.data["status"] == "completed"
        assert result.tool_name == "test_mcp"
        assert result.metadata["mcp_tool"] == "git_execute"

        # Verify MCP connector was called correctly
        mock_connector.execute_tool.assert_called_once_with(
            tool_name="git_execute", command="git status", repo_path="/test/repo"
        )

    @pytest.mark.asyncio
    @patch("mycoder.tool_registry.MCPConnector")
    async def test_execute_orchestrator_unavailable(self, mock_mcp_connector_class):
        """Test execution when MCP orchestrator is unavailable"""
        # Mock MCP connector with unavailable orchestrator
        mock_connector = AsyncMock()
        mock_connector.is_orchestrator_available.return_value = False
        mock_mcp_connector_class.return_value = mock_connector

        tool = self.create_tool()
        context = ToolExecutionContext(mode="FULL")

        result = await tool.execute(context)

        assert result.success is False
        assert "MCP orchestrator not available" in result.error

    @pytest.mark.asyncio
    @patch("mycoder.tool_registry.MCPConnector")
    async def test_execute_mcp_error(self, mock_mcp_connector_class):
        """Test execution when MCP operation fails"""
        # Mock MCP connector with error
        mock_connector = AsyncMock()
        mock_connector.is_orchestrator_available.return_value = True
        mock_connector.execute_tool.side_effect = Exception("MCP execution failed")
        mock_mcp_connector_class.return_value = mock_connector

        tool = self.create_tool()
        context = ToolExecutionContext(mode="FULL")

        result = await tool.execute(context)

        assert result.success is False
        assert "MCP execution failed" in result.error


class TestThermalAwareTool:
    """Test ThermalAwareTool implementation"""

    def create_tool(self):
        """Create thermal-aware tool"""

        class TestThermalTool(ThermalAwareTool):
            async def _execute_core_logic(self, context, **kwargs):
                return {"result": "thermal-safe operation completed"}

        return TestThermalTool("thermal_test", ToolCategory.AI_OPERATIONS)

    def test_tool_initialization(self):
        """Test thermal-aware tool initialization"""
        tool = self.create_tool()

        assert tool.name == "thermal_test"
        assert tool.category == ToolCategory.AI_OPERATIONS
        assert tool.availability == ToolAvailability.LOCAL_ONLY
        assert tool.priority == ToolPriority.LOW
        assert tool.capabilities.requires_thermal_safe is True
        assert tool.capabilities.resource_intensive is True
        assert tool.capabilities.max_execution_time == 120

    @pytest.mark.asyncio
    async def test_check_thermal_status_from_context(self):
        """Test thermal status check from context"""
        tool = self.create_tool()

        context = ToolExecutionContext(
            mode="AUTONOMOUS", thermal_status={"cpu_temp": 75, "safe_operation": True}
        )

        is_safe = await tool._check_thermal_status(context)
        assert is_safe is True

    @pytest.mark.asyncio
    async def test_check_thermal_status_unsafe_from_context(self):
        """Test thermal status check when unsafe"""
        tool = self.create_tool()

        context = ToolExecutionContext(
            mode="AUTONOMOUS", thermal_status={"cpu_temp": 85, "safe_operation": False}
        )

        is_safe = await tool._check_thermal_status(context)
        assert is_safe is False

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    async def test_check_thermal_status_script_success(self, mock_subprocess):
        """Test thermal status check via script"""
        # Mock successful thermal script
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (
            b"Temperature: 75\xc2\xb0C - NORMAL operation",
            b"",
        )
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        tool = self.create_tool()
        context = ToolExecutionContext(mode="AUTONOMOUS")

        is_safe = await tool._check_thermal_status(context)
        assert is_safe is True

    @pytest.mark.asyncio
    @patch("os.path.exists", return_value=True)
    @patch("os.environ.get", return_value="/fake/thermal_script.sh")
    @patch("asyncio.create_subprocess_exec")
    async def test_check_thermal_status_script_critical(
        self, mock_subprocess, mock_env, mock_exists
    ):
        """Test thermal status check with critical temperature"""
        # Mock thermal script indicating critical temperature
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (
            b"Temperature: 87\xc2\xb0C - CRITICAL - throttling required",
            b"",
        )
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        tool = self.create_tool()
        context = ToolExecutionContext(mode="AUTONOMOUS")

        is_safe = await tool._check_thermal_status(context)
        assert is_safe is False

    @pytest.mark.asyncio
    @patch("asyncio.create_subprocess_exec")
    async def test_check_thermal_status_script_error(self, mock_subprocess):
        """Test thermal status check when script fails"""
        # Mock script failure
        mock_subprocess.side_effect = Exception("Script not found")

        tool = self.create_tool()
        context = ToolExecutionContext(mode="AUTONOMOUS")

        is_safe = await tool._check_thermal_status(context)
        assert is_safe is True  # Assume safe on error

    @pytest.mark.asyncio
    async def test_execute_success_thermal_safe(self):
        """Test successful execution when thermal safe"""
        tool = self.create_tool()

        context = ToolExecutionContext(
            mode="AUTONOMOUS", thermal_status={"cpu_temp": 70, "safe_operation": True}
        )

        result = await tool.execute(context, test_param="value")

        assert result.success is True
        assert result.data["result"] == "thermal-safe operation completed"
        assert result.metadata["thermal_safe"] is True

    @pytest.mark.asyncio
    async def test_execute_blocked_thermal_unsafe(self):
        """Test execution blocked when thermal unsafe"""
        tool = self.create_tool()

        context = ToolExecutionContext(
            mode="AUTONOMOUS", thermal_status={"cpu_temp": 90, "safe_operation": False}
        )

        result = await tool.execute(context)

        assert result.success is False
        assert "Thermal limits exceeded" in result.error

    @pytest.mark.asyncio
    async def test_validate_context_thermal_safe(self):
        """Test context validation when thermal safe"""
        tool = self.create_tool()

        context = ToolExecutionContext(
            mode="AUTONOMOUS", thermal_status={"cpu_temp": 65}
        )

        is_valid = await tool.validate_context(context)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_context_thermal_unsafe(self):
        """Test context validation when thermal unsafe"""
        tool = self.create_tool()

        context = ToolExecutionContext(
            mode="AUTONOMOUS", thermal_status={"cpu_temp": 95}
        )

        is_valid = await tool.validate_context(context)
        assert is_valid is False


class TestToolRegistry:
    """Test ToolRegistry main class"""

    def create_registry(self):
        """Create fresh registry for testing"""
        return ToolRegistry()

    def test_registry_initialization(self):
        """Test registry initialization with core tools"""
        registry = self.create_registry()

        # Check that core tools are registered
        assert "file_read" in registry.tools
        assert "file_write" in registry.tools
        assert "file_list" in registry.tools

        # Check categories are organized
        assert ToolCategory.FILE_OPERATIONS in registry.categories
        assert len(registry.categories[ToolCategory.FILE_OPERATIONS]) >= 3

    def test_register_tool(self):
        """Test tool registration"""
        registry = self.create_registry()

        # Create custom tool
        capabilities = ToolCapabilities(requires_network=True)
        custom_tool = BaseTool(
            name="custom_tool",
            category=ToolCategory.COMMUNICATION,
            availability=ToolAvailability.FULL_ONLY,
            priority=ToolPriority.HIGH,
            capabilities=capabilities,
        )

        # Mock abstract methods
        custom_tool.execute = AsyncMock()
        custom_tool.validate_context = AsyncMock()

        initial_count = len(registry.tools)
        registry.register_tool(custom_tool)

        assert len(registry.tools) == initial_count + 1
        assert "custom_tool" in registry.tools
        assert ToolCategory.COMMUNICATION in registry.categories
        assert "custom_tool" in registry.categories[ToolCategory.COMMUNICATION]

    def test_register_duplicate_tool(self):
        """Test registering tool with duplicate name"""
        registry = self.create_registry()

        # Create two tools with same name
        capabilities = ToolCapabilities()

        tool1 = BaseTool(
            name="duplicate",
            category=ToolCategory.FILE_OPERATIONS,
            availability=ToolAvailability.ALWAYS,
            priority=ToolPriority.NORMAL,
            capabilities=capabilities,
        )
        tool1.execute = AsyncMock()
        tool1.validate_context = AsyncMock()

        tool2 = BaseTool(
            name="duplicate",
            category=ToolCategory.GIT_OPERATIONS,
            availability=ToolAvailability.FULL_ONLY,
            priority=ToolPriority.HIGH,
            capabilities=capabilities,
        )
        tool2.execute = AsyncMock()
        tool2.validate_context = AsyncMock()

        registry.register_tool(tool1)
        initial_count = len(registry.tools)

        # Should replace existing tool
        registry.register_tool(tool2)

        assert len(registry.tools) == initial_count
        assert registry.tools["duplicate"].category == ToolCategory.GIT_OPERATIONS

    def test_unregister_tool(self):
        """Test tool unregistration"""
        registry = self.create_registry()
        initial_count = len(registry.tools)

        # Unregister existing tool
        registry.unregister_tool("file_read")

        assert len(registry.tools) == initial_count - 1
        assert "file_read" not in registry.tools

        # Verify it's removed from category
        file_ops_tools = registry.categories.get(ToolCategory.FILE_OPERATIONS, [])
        assert "file_read" not in file_ops_tools

    def test_unregister_nonexistent_tool(self):
        """Test unregistering non-existent tool"""
        registry = self.create_registry()
        initial_count = len(registry.tools)

        # Should not raise error
        registry.unregister_tool("nonexistent_tool")

        assert len(registry.tools) == initial_count

    @pytest.mark.asyncio
    async def test_execute_tool_success(self):
        """Test successful tool execution"""
        registry = self.create_registry()

        with TemporaryDirectory() as temp_dir:
            context = ToolExecutionContext(
                mode="FULL", working_directory=Path(temp_dir)
            )

            # Create test file
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("Hello World")

            result = await registry.execute_tool(
                "file_read", context, operation="read", path="test.txt"
            )

            assert result.success is True
            assert result.data == "Hello World"
            assert result.tool_name == "file_read"

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self):
        """Test executing non-existent tool"""
        registry = self.create_registry()
        context = ToolExecutionContext(mode="FULL")

        result = await registry.execute_tool("nonexistent_tool", context)

        assert result.success is False
        assert "Tool nonexistent_tool not found" in result.error

    @pytest.mark.asyncio
    async def test_execute_tool_wrong_mode(self):
        """Test executing tool in wrong mode"""
        registry = self.create_registry()

        # Create tool that only works in FULL mode
        capabilities = ToolCapabilities()
        full_mode_tool = BaseTool(
            name="full_mode_only",
            category=ToolCategory.RESEARCH_OPERATIONS,
            availability=ToolAvailability.FULL_ONLY,
            priority=ToolPriority.NORMAL,
            capabilities=capabilities,
        )
        full_mode_tool.execute = AsyncMock()
        full_mode_tool.validate_context = AsyncMock()

        registry.register_tool(full_mode_tool)

        # Try to execute in RECOVERY mode
        context = ToolExecutionContext(mode="RECOVERY")
        result = await registry.execute_tool("full_mode_only", context)

        assert result.success is False
        assert "not available in RECOVERY mode" in result.error

    @pytest.mark.asyncio
    async def test_execute_tool_context_validation_failure(self):
        """Test tool execution with context validation failure"""
        registry = self.create_registry()

        # File operation tool requires working directory
        context = ToolExecutionContext(mode="FULL")  # No working directory

        result = await registry.execute_tool("file_read", context, path="test.txt")

        assert result.success is False
        assert "Context validation failed" in result.error

    @pytest.mark.asyncio
    async def test_execute_tool_execution_error(self):
        """Test tool execution with runtime error"""
        registry = self.create_registry()

        with TemporaryDirectory() as temp_dir:
            context = ToolExecutionContext(
                mode="FULL", working_directory=Path(temp_dir)
            )

            # Try to read non-existent file
            result = await registry.execute_tool(
                "file_read", context, operation="read", path="nonexistent.txt"
            )

            assert result.success is False
            assert "File not found" in result.error

    def test_get_tools_for_mode(self):
        """Test getting tools available for specific mode"""
        registry = self.create_registry()

        # Get tools for FULL mode
        full_mode_tools = registry.get_tools_for_mode("FULL")
        assert "file_read" in full_mode_tools
        assert "file_write" in full_mode_tools
        assert "file_list" in full_mode_tools

        # Get tools for RECOVERY mode
        recovery_mode_tools = registry.get_tools_for_mode("RECOVERY")
        assert "file_read" in recovery_mode_tools  # Available in all modes

    def test_get_tools_by_category(self):
        """Test getting tools by category"""
        registry = self.create_registry()

        file_ops_tools = registry.get_tools_by_category(ToolCategory.FILE_OPERATIONS)
        assert "file_read" in file_ops_tools
        assert "file_write" in file_ops_tools
        assert "file_list" in file_ops_tools

        # Non-existent category
        empty_category_tools = registry.get_tools_by_category(
            ToolCategory.DATABASE_OPERATIONS
        )
        assert empty_category_tools == []

    def test_get_tool_info(self):
        """Test getting detailed tool information"""
        registry = self.create_registry()

        info = registry.get_tool_info("file_read")

        assert info is not None
        assert info["name"] == "file_read"
        assert info["category"] == "file_operations"
        assert info["availability"] == "always"
        assert info["priority"] == "high"
        assert "capabilities" in info
        assert "metrics" in info

        # Non-existent tool
        assert registry.get_tool_info("nonexistent") is None

    def test_get_registry_stats(self):
        """Test getting registry statistics"""
        registry = self.create_registry()

        stats = registry.get_registry_stats()

        assert "total_tools" in stats
        assert "categories" in stats
        assert "total_executions" in stats
        assert "total_errors" in stats
        assert "success_rate" in stats

        assert stats["total_tools"] >= 3  # At least the core tools
        assert "file_operations" in stats["categories"]
        assert stats["categories"]["file_operations"] >= 3

    def test_event_handlers(self):
        """Test event handler system"""
        registry = self.create_registry()

        # Track events
        events_received = []

        def event_handler(event_type, data):
            events_received.append((event_type, data))

        registry.add_event_handler("tool_registered", event_handler)
        registry.add_event_handler("tool_unregistered", event_handler)

        # Register a tool to trigger event
        capabilities = ToolCapabilities()
        test_tool = BaseTool(
            name="event_test",
            category=ToolCategory.SYSTEM_MONITORING,
            availability=ToolAvailability.ALWAYS,
            priority=ToolPriority.NORMAL,
            capabilities=capabilities,
        )
        test_tool.execute = AsyncMock()
        test_tool.validate_context = AsyncMock()

        registry.register_tool(test_tool)

        # Check registration event
        assert len(events_received) == 1
        assert events_received[0][0] == "tool_registered"
        assert events_received[0][1]["tool"].name == "event_test"

        # Unregister to trigger unregistration event
        registry.unregister_tool("event_test")

        # Check unregistration event
        assert len(events_received) == 2
        assert events_received[1][0] == "tool_unregistered"
        assert events_received[1][1]["tool_name"] == "event_test"


class TestGlobalRegistry:
    """Test global registry functions"""

    def test_get_tool_registry_singleton(self):
        """Test global registry singleton behavior"""
        registry1 = get_tool_registry()
        registry2 = get_tool_registry()

        assert registry1 is registry2  # Same instance
        assert isinstance(registry1, ToolRegistry)

    def test_global_registry_persistence(self):
        """Test that global registry persists data"""
        registry = get_tool_registry()
        initial_count = len(registry.tools)

        # Add a tool
        capabilities = ToolCapabilities()
        test_tool = BaseTool(
            name="persistent_test",
            category=ToolCategory.SYSTEM_MONITORING,
            availability=ToolAvailability.ALWAYS,
            priority=ToolPriority.NORMAL,
            capabilities=capabilities,
        )
        test_tool.execute = AsyncMock()
        test_tool.validate_context = AsyncMock()

        registry.register_tool(test_tool)

        # Get registry again
        registry2 = get_tool_registry()
        assert len(registry2.tools) == initial_count + 1
        assert "persistent_test" in registry2.tools


@pytest.mark.integration
class TestToolRegistryIntegration:
    """Integration tests for tool registry with real systems"""

    @pytest.mark.asyncio
    async def test_file_operations_integration(self):
        """Test file operations with real filesystem"""
        registry = get_tool_registry()

        with TemporaryDirectory() as temp_dir:
            context = ToolExecutionContext(
                mode="FULL", working_directory=Path(temp_dir)
            )

            # Test complete file operation workflow

            # 1. Write a file
            write_result = await registry.execute_tool(
                "file_write",
                context,
                operation="write",
                path="integration_test.txt",
                content="This is an integration test",
            )

            assert write_result.success is True

            # 2. Check file exists
            exists_result = await registry.execute_tool(
                "file_read", context, operation="exists", path="integration_test.txt"
            )

            assert exists_result.success is True
            assert exists_result.data is True

            # 3. Read the file
            read_result = await registry.execute_tool(
                "file_read", context, operation="read", path="integration_test.txt"
            )

            assert read_result.success is True
            assert read_result.data == "This is an integration test"

            # 4. List directory
            list_result = await registry.execute_tool(
                "file_list", context, operation="list", path="."
            )

            assert list_result.success is True
            assert any("integration_test.txt" in str(item) for item in list_result.data)

    @pytest.mark.asyncio
    async def test_thermal_integration_real(self):
        """Test thermal integration with real Q9550 system"""
        # Skip if thermal management script not available
        thermal_script = Path(
            "/home/milhy777/Develop/Production/PowerManagement/scripts/"
            "performance_manager.sh"
        )
        if not thermal_script.exists():
            pytest.skip("Thermal management script not available")

        class TestThermalIntegration(ThermalAwareTool):
            async def _execute_core_logic(self, context, **kwargs):
                return {"temp_check": "passed", "system": "Q9550"}

        tool = TestThermalIntegration(
            "real_thermal_test", ToolCategory.THERMAL_MANAGEMENT
        )
        registry = get_tool_registry()
        registry.register_tool(tool)

        context = ToolExecutionContext(mode="AUTONOMOUS")
        result = await registry.execute_tool("real_thermal_test", context)

        # Should either succeed (if thermal safe) or fail with thermal error
        if result.success:
            assert result.data["temp_check"] == "passed"
            assert result.metadata["thermal_safe"] is True
        else:
            assert "Thermal limits exceeded" in result.error

    @pytest.mark.asyncio
    async def test_registry_performance(self):
        """Test registry performance with many tools and operations"""
        registry = get_tool_registry()

        # Register many tools
        for i in range(100):
            capabilities = ToolCapabilities()
            tool = BaseTool(
                name=f"perf_test_{i}",
                category=ToolCategory.SYSTEM_MONITORING,
                availability=ToolAvailability.ALWAYS,
                priority=ToolPriority.NORMAL,
                capabilities=capabilities,
            )

            async def mock_execute(context, **kwargs):
                return ToolResult(
                    success=True,
                    data=f"result_{i}",
                    tool_name=f"perf_test_{i}",
                    duration_ms=1,
                )

            tool.execute = mock_execute
            tool.validate_context = AsyncMock(return_value=True)

            registry.register_tool(tool)

        # Test rapid tool executions
        context = ToolExecutionContext(mode="FULL")

        start_time = time.time()
        tasks = []

        for i in range(50):
            task = registry.execute_tool(f"perf_test_{i}", context)
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # All should succeed
        assert all(result.success for result in results)

        # Should complete reasonably quickly
        assert end_time - start_time < 5.0  # Less than 5 seconds for 50 operations

        # Clean up
        for i in range(100):
            registry.unregister_tool(f"perf_test_{i}")
