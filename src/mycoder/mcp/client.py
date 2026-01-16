"""MCP Client for connecting to MCP servers."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .protocol import MCPTool


@dataclass
class MCPServerConnection:
    name: str
    process: asyncio.subprocess.Process


class MCPClient:
    """Client for communicating with MCP servers."""

    def __init__(self) -> None:
        self.servers: Dict[str, MCPServerConnection] = {}
        self.available_tools: Dict[str, MCPTool] = {}

    async def connect(self, server_name: str, command: List[str]) -> bool:
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self.servers[server_name] = MCPServerConnection(
                name=server_name, process=process
            )
            tools = await self._initialize_server(server_name)
            for tool in tools:
                self.available_tools[f"{server_name}:{tool.name}"] = tool
            return True
        except Exception:
            return False

    async def _initialize_server(self, server_name: str) -> List[MCPTool]:
        conn = self.servers.get(server_name)
        if not conn:
            return []

        await self._send_request(server_name, "initialize", {"capabilities": {}})
        tools_response = await self._send_request(server_name, "tools/list", {})
        tools = []
        for tool_data in tools_response.get("tools", []):
            tools.append(
                MCPTool(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    parameters=tool_data.get("inputSchema", {}).get("properties", {}),
                )
            )
        return tools

    async def call_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        if ":" in tool_name:
            server_name, tool = tool_name.split(":", 1)
        else:
            for full_name in self.available_tools:
                if full_name.endswith(f":{tool_name}"):
                    server_name, tool = full_name.split(":", 1)
                    break
            else:
                return {"error": f"Tool not found: {tool_name}"}

        return await self._send_request(
            server_name, "tools/call", {"name": tool, "arguments": arguments}
        )

    async def _send_request(
        self, server_name: str, method: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        conn = self.servers.get(server_name)
        if not conn or not conn.process.stdin:
            return {"error": "Server not connected"}

        import uuid

        request_id = str(uuid.uuid4())
        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        conn.process.stdin.write((json.dumps(message) + "\n").encode())
        await conn.process.stdin.drain()

        if conn.process.stdout:
            line = await conn.process.stdout.readline()
            response = json.loads(line.decode())
            return response.get("result", {})

        return {}

    def get_available_tools(self) -> List[MCPTool]:
        return list(self.available_tools.values())
