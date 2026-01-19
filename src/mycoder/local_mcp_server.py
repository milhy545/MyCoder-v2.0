"""Local MCP server with basic tools for offline use."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from aiohttp import web

logger = logging.getLogger(__name__)


class LocalMemoryStore:
    """Simple JSONL memory store for local MCP usage."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memory_path = self.data_dir / "mcp_memory.jsonl"

    def append(self, entry: Dict[str, Any]) -> None:
        with self.memory_path.open("a", encoding="utf-8") as handle:
            json.dump(entry, handle, ensure_ascii=True)
            handle.write("\n")

    def search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        if not self.memory_path.exists() or not query:
            return []

        results = []
        query_lower = query.lower()
        with self.memory_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                content = str(entry.get("content", ""))
                if query_lower in content.lower():
                    results.append(entry)

        results.sort(key=lambda item: item.get("importance", 0), reverse=True)
        return results[:limit]


class LocalMCPServer:
    """Minimal MCP-compatible server with filesystem, git, terminal, and memory."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8020,
        data_dir: Optional[Path] = None,
    ):
        self.host = host
        self.port = port
        self.data_dir = data_dir or Path.home() / ".mycoder"
        self.memory_store = LocalMemoryStore(self.data_dir)
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self._register_routes()

    def _register_routes(self) -> None:
        self.app.router.add_get("/health", self._handle_health)
        self.app.router.add_get("/services", self._handle_services)
        self.app.router.add_post("/mcp", self._handle_mcp)

    async def start(self) -> None:
        if self.runner:
            return
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        logger.info("Local MCP server running at http://%s:%s", self.host, self.port)

    async def stop(self) -> None:
        if self.runner:
            await self.runner.cleanup()
            self.runner = None
            self.site = None

    async def _handle_health(self, request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    async def _handle_services(self, request: web.Request) -> web.Response:
        services = {
            "filesystem": {
                "status": "running",
                "tools": [
                    "file_read",
                    "file_write",
                    "file_list",
                    "file_search",
                ],
            },
            "terminal": {
                "status": "running",
                "tools": [
                    "terminal_exec",
                    "shell_command",
                    "system_info",
                ],
            },
            "git": {
                "status": "running",
                "tools": [
                    "git_status",
                    "git_diff",
                    "git_log",
                ],
            },
            "memory": {
                "status": "running",
                "tools": [
                    "store_memory",
                    "search_memories",
                ],
            },
        }
        payload = {"zen_coordinator": {"services": services}}
        return web.json_response(payload)

    async def _handle_mcp(self, request: web.Request) -> web.Response:
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.json_response({"error": "Invalid JSON payload"}, status=400)

        tool = data.get("tool")
        args = data.get("arguments") or {}

        handler = {
            "file_read": self._tool_file_read,
            "file_write": self._tool_file_write,
            "file_list": self._tool_file_list,
            "file_search": self._tool_file_search,
            "terminal_exec": self._tool_terminal_exec,
            "shell_command": self._tool_terminal_exec,
            "system_info": self._tool_system_info,
            "git_status": self._tool_git_status,
            "git_diff": self._tool_git_diff,
            "git_log": self._tool_git_log,
            "store_memory": self._tool_store_memory,
            "search_memories": self._tool_search_memories,
        }.get(tool)

        if not handler:
            return web.json_response({"error": f"Unknown tool: {tool}"}, status=400)

        try:
            result = await handler(args)
        except (FileNotFoundError, ValueError) as exc:
            return web.json_response({"error": str(exc)}, status=400)
        except Exception as exc:
            safe_tool = repr(tool).replace("\r", "").replace("\n", "")
            logger.exception("Local MCP tool failure: %s", safe_tool)
            return web.json_response({"error": str(exc)}, status=500)

        return web.json_response(result)

    async def _tool_file_read(self, args: Dict[str, Any]) -> Dict[str, Any]:
        path = self._resolve_path(args.get("path"))
        if not path or not path.exists():
            raise FileNotFoundError("File not found")
        content = path.read_text(encoding="utf-8", errors="replace")
        return {"path": str(path), "content": content}

    async def _tool_file_write(self, args: Dict[str, Any]) -> Dict[str, Any]:
        path = self._resolve_path(args.get("path"))
        content = args.get("content", "")
        if not path:
            raise FileNotFoundError("Path not provided")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(content), encoding="utf-8")
        return {"path": str(path), "written": True}

    async def _tool_file_list(self, args: Dict[str, Any]) -> Dict[str, Any]:
        path = self._resolve_path(args.get("path", "."))
        recursive = bool(args.get("recursive", False))
        max_entries = int(args.get("max_entries", 500))
        if not path or not path.exists():
            raise FileNotFoundError("Path not found")

        entries = []
        if recursive:
            for entry in path.rglob("*"):
                entries.append(str(entry))
                if len(entries) >= max_entries:
                    break
        else:
            for entry in path.iterdir():
                entries.append(str(entry))
                if len(entries) >= max_entries:
                    break

        return {"path": str(path), "entries": entries}

    async def _tool_file_search(self, args: Dict[str, Any]) -> Dict[str, Any]:
        query = str(args.get("query", "")).strip()
        path = self._resolve_path(args.get("path", "."))
        max_results = int(args.get("max_results", 50))
        if not query:
            raise ValueError("Query is required")
        if not path or not path.exists():
            raise FileNotFoundError("Path not found")

        if shutil.which("rg"):
            return await self._rg_search(query, path, max_results)
        return self._python_search(query, path, max_results)

    async def _tool_terminal_exec(self, args: Dict[str, Any]) -> Dict[str, Any]:
        command = args.get("command") or args.get("cmd")
        if not command:
            raise ValueError("Command is required")
        working_dir = args.get("working_dir") or args.get("cwd")
        timeout = int(args.get("timeout", 30))
        result = await self._run_command(str(command), working_dir, timeout)
        return result

    async def _tool_system_info(self, args: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "cwd": str(Path.cwd()),
            "python": os.sys.version.split()[0],
            "time": time.time(),
        }

    async def _tool_git_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        repo_path = self._resolve_path(args.get("repo_path", "."))
        return await self._run_command(
            f"git -C {self._shell_quote(repo_path)} status --porcelain",
            None,
            int(args.get("timeout", 30)),
        )

    async def _tool_git_diff(self, args: Dict[str, Any]) -> Dict[str, Any]:
        repo_path = self._resolve_path(args.get("repo_path", "."))
        return await self._run_command(
            f"git -C {self._shell_quote(repo_path)} diff",
            None,
            int(args.get("timeout", 30)),
        )

    async def _tool_git_log(self, args: Dict[str, Any]) -> Dict[str, Any]:
        repo_path = self._resolve_path(args.get("repo_path", "."))
        limit = int(args.get("limit", 10))
        return await self._run_command(
            f"git -C {self._shell_quote(repo_path)} log -n {limit} --oneline",
            None,
            int(args.get("timeout", 30)),
        )

    async def _tool_store_memory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        content = str(args.get("content", "")).strip()
        if not content:
            raise ValueError("Content is required")
        entry = {
            "content": content,
            "type": args.get("type", "interaction"),
            "importance": float(args.get("importance", 0.5)),
            "timestamp": time.time(),
        }
        self.memory_store.append(entry)
        return {"stored": True}

    async def _tool_search_memories(self, args: Dict[str, Any]) -> Dict[str, Any]:
        query = str(args.get("query", "")).strip()
        limit = int(args.get("limit", 5))
        memories = self.memory_store.search(query, limit)
        return {"memories": memories}

    async def _rg_search(
        self, query: str, path: Path, max_results: int
    ) -> Dict[str, Any]:
        cmd = f"rg -n --no-heading --color=never {self._shell_quote(query)} {self._shell_quote(path)}"
        result = await self._run_command(cmd, None, 30)
        matches = []
        if result.get("returncode") == 0:
            for line in result.get("stdout", "").splitlines():
                parts = line.split(":", 2)
                if len(parts) < 3:
                    continue
                match = {
                    "path": parts[0],
                    "line": int(parts[1]) if parts[1].isdigit() else None,
                    "text": parts[2],
                }
                matches.append(match)
                if len(matches) >= max_results:
                    break
        return {"matches": matches}

    def _python_search(
        self, query: str, path: Path, max_results: int
    ) -> Dict[str, Any]:
        matches = []
        for file_path in path.rglob("*"):
            if not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for idx, line in enumerate(content.splitlines(), start=1):
                if query.lower() in line.lower():
                    matches.append({"path": str(file_path), "line": idx, "text": line})
                    if len(matches) >= max_results:
                        return {"matches": matches}
        return {"matches": matches}

    async def _run_command(
        self, command: str, working_dir: Optional[str], timeout: int
    ) -> Dict[str, Any]:
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
        except asyncio.TimeoutError:
            process.kill()
            return {"stdout": "", "stderr": "Command timed out", "returncode": 124}

        return {
            "stdout": stdout.decode("utf-8", errors="replace"),
            "stderr": stderr.decode("utf-8", errors="replace"),
            "returncode": process.returncode,
        }

    def _resolve_path(self, raw_path: Optional[str]) -> Optional[Path]:
        if not raw_path:
            return None
        path = Path(str(raw_path)).expanduser()
        if not path.is_absolute():
            path = Path.cwd() / path
        return path

    def _shell_quote(self, value: Path | str) -> str:
        text = str(value)
        return "'" + text.replace("'", "'\"'\"'") + "'"


def main() -> None:
    parser = argparse.ArgumentParser(description="Local MCP server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8020)
    parser.add_argument("--data-dir", default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
    data_dir = Path(args.data_dir).expanduser() if args.data_dir else None
    server = LocalMCPServer(host=args.host, port=args.port, data_dir=data_dir)

    async def _run() -> None:
        await server.start()
        while True:
            await asyncio.sleep(3600)

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
