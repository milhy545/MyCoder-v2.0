"""Integration tests ensuring FailureMemory interacts with ToolRegistry."""

from pathlib import Path

import pytest

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


class AlwaysFailTool(BaseTool):
    def __init__(self, name: str):
        super().__init__(
            name=name,
            category=ToolCategory.FILE_OPERATIONS,
            availability=ToolAvailability.ALWAYS,
            priority=ToolPriority.NORMAL,
            capabilities=ToolCapabilities(),
        )

    async def validate_context(self, context: ToolExecutionContext) -> bool:
        return True

    async def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        return ToolResult(
            success=False,
            data=None,
            tool_name=self.name,
            duration_ms=0,
            error="simulated failure",
        )


class ToggleTool(BaseTool):
    def __init__(self, name: str):
        super().__init__(
            name=name,
            category=ToolCategory.FILE_OPERATIONS,
            availability=ToolAvailability.ALWAYS,
            priority=ToolPriority.NORMAL,
            capabilities=ToolCapabilities(),
        )
        self._failed = False

    async def validate_context(self, context: ToolExecutionContext) -> bool:
        return True

    async def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        if not self._failed:
            self._failed = True
            return ToolResult(
                success=False,
                data=None,
                tool_name=self.name,
                duration_ms=0,
                error="simulated fail-first",
            )

        return ToolResult(
            success=True,
            data={"status": "ok"},
            tool_name=self.name,
            duration_ms=0,
        )


def make_context(tmp_path: Path, mode: str = "FULL") -> ToolExecutionContext:
    return ToolExecutionContext(mode=mode, working_directory=tmp_path)


@pytest.mark.asyncio
async def test_tool_registry_blocks_repeated_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("MYCODER_LOCAL_MEMORY_DB", str(tmp_path / "failure_memory.db"))
    registry = ToolRegistry()
    registry.register_tool(AlwaysFailTool("failing_tool"))

    context = make_context(tmp_path)

    for _ in range(3):
        result = await registry.execute_tool("failing_tool", context)
        assert not result.success

    blocked = await registry.execute_tool("failing_tool", context)
    assert not blocked.success
    assert blocked.error and "BLOCKED by FailureMemory" in blocked.error


@pytest.mark.asyncio
async def test_tool_registry_allows_different_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("MYCODER_LOCAL_MEMORY_DB", str(tmp_path / "failure_memory.db"))
    registry = ToolRegistry()
    registry.register_tool(AlwaysFailTool("env_tool"))

    context1 = make_context(tmp_path / "env1")
    context2 = make_context(tmp_path / "env2")

    for _ in range(3):
        await registry.execute_tool("env_tool", context1)

    result = await registry.execute_tool("env_tool", context2)
    assert not result.success
    assert result.error and "BLOCKED" not in result.error


@pytest.mark.asyncio
async def test_tool_registry_clears_on_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("MYCODER_LOCAL_MEMORY_DB", str(tmp_path / "failure_memory.db"))
    registry = ToolRegistry()
    registry.register_tool(ToggleTool("toggle_tool"))

    context = make_context(tmp_path)

    first = await registry.execute_tool("toggle_tool", context)
    assert not first.success

    second = await registry.execute_tool("toggle_tool", context)
    assert second.success

    third = await registry.execute_tool("toggle_tool", context)
    assert third.success
