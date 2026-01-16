from mycoder.mcp.protocol import MCPMessage, MCPMessageType, MCPTool


def test_mcp_tool_to_dict() -> None:
    tool = MCPTool(name="tool", description="desc", parameters={"q": {"type": "string"}})

    payload = tool.to_dict()

    assert payload["name"] == "tool"
    assert payload["description"] == "desc"
    assert payload["inputSchema"]["properties"]["q"]["type"] == "string"


def test_mcp_message_fields() -> None:
    msg = MCPMessage(
        type=MCPMessageType.REQUEST,
        method="tools/list",
        params={"foo": "bar"},
        id="1",
    )

    assert msg.type == MCPMessageType.REQUEST
    assert msg.method == "tools/list"
    assert msg.params == {"foo": "bar"}
