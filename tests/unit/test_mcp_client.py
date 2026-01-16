import pytest

from mycoder.mcp.client import MCPClient


@pytest.mark.asyncio
async def test_call_tool_missing_returns_error() -> None:
    client = MCPClient()

    result = await client.call_tool("missing", {})

    assert "error" in result


def test_get_available_tools_empty() -> None:
    client = MCPClient()

    tools = client.get_available_tools()

    assert tools == []
