"""
Command Parser for MyCoder v2.1.1

Parsuje uživatelské CLI příkazy na strukturované Command objekty
pro spuštění nástrojů přes tool_registry.
"""

import logging
import re
import shlex
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class Command:
    """Strukturovaný příkaz pro tool execution"""

    tool: str  # Název nástroje ("terminal_exec", "file_read", etc.)
    args: Dict[str, Any]  # Argumenty pro nástroj
    raw_input: str  # Původní uživatelský vstup


class CommandParser:
    """Parser pro CLI příkazy MyCoder"""

    def __init__(self):
        self.command_patterns = {
            # Bash/Terminal commands
            r"^/bash\s+(.+)$": self._parse_bash_command,
            r"^/sh\s+(.+)$": self._parse_bash_command,
            r"^/exec\s+(.+)$": self._parse_bash_command,
            # File operations
            r"^/file\s+read\s+(.+)$": self._parse_file_read,
            r"^/file\s+write\s+(.+)$": self._parse_file_write,
            r"^/file\s+list\s*(.*)$": self._parse_file_list,
            r"^/read\s+(.+)$": self._parse_file_read,  # Shortcut
            r"^/write\s+(.+)$": self._parse_file_write,  # Shortcut
            r"^/edit\s+(.+)$": self._parse_file_edit,
            # Git operations
            r"^/git\s+status$": self._parse_git_status,
            r"^/git\s+diff\s*(.*)$": self._parse_git_diff,
            r"^/git\s+log\s*(.*)$": self._parse_git_log,
            r"^/git\s+add\s+(.+)$": self._parse_git_add,
            r"^/git\s+commit\s+(.+)$": self._parse_git_commit,
            # Provider control
            r"^/provider\s+(\w+)$": self._parse_provider_override,
        }

    def parse(self, user_input: str) -> Optional[Command]:
        """
        Parsuje uživatelský vstup na Command objekt.

        Args:
            user_input: Vstup od uživatele (např. "/bash ls -la")

        Returns:
            Command objekt nebo None pokud není rozpoznán jako příkaz
        """
        if not user_input or not user_input.startswith("/"):
            return None

        user_input = user_input.strip()

        # Zkus každý pattern
        for pattern, parser_func in self.command_patterns.items():
            match = re.match(pattern, user_input, re.IGNORECASE)
            if match:
                try:
                    return parser_func(match, user_input)
                except Exception as e:
                    logger.error(f"Error parsing command '{user_input}': {e}")
                    return None

        # Nerozpoznaný příkaz
        return None

    def _parse_bash_command(self, match: re.Match, raw_input: str) -> Command:
        """Parse /bash <command>"""
        command_str = match.group(1).strip()
        return Command(
            tool="terminal_exec", args={"command": command_str}, raw_input=raw_input
        )

    def _parse_file_read(self, match: re.Match, raw_input: str) -> Command:
        """Parse /file read <path> nebo /read <path>"""
        file_path = match.group(1).strip()
        return Command(tool="file_read", args={"path": file_path}, raw_input=raw_input)

    def _parse_file_write(self, match: re.Match, raw_input: str) -> Command:
        """Parse /file write <path> nebo /write <path>"""
        # Očekáváme: /file write <path> následovaný obsahem v další interakci
        # Zatím jen path
        file_path = match.group(1).strip()
        return Command(
            tool="file_write",
            args={"path": file_path, "content": ""},  # Content bude doplněn později
            raw_input=raw_input,
        )

    def _parse_file_list(self, match: re.Match, raw_input: str) -> Command:
        """Parse /file list [directory]"""
        directory = match.group(1).strip() or "."
        return Command(
            tool="file_list", args={"directory": directory}, raw_input=raw_input
        )

    def _parse_file_edit(self, match: re.Match, raw_input: str) -> Command:
        """Parse /edit <path> "<old>" "<new>" [--all]"""
        parts = shlex.split(match.group(1).strip())
        replace_all = False
        filtered = []
        for part in parts:
            if part == "--all":
                replace_all = True
            else:
                filtered.append(part)

        if len(filtered) < 3:
            return Command(
                tool="file_edit",
                args={
                    "path": "",
                    "old_string": None,
                    "new_string": None,
                    "replace_all": replace_all,
                },
                raw_input=raw_input,
            )

        path, old_string, new_string = filtered[0], filtered[1], filtered[2]
        return Command(
            tool="file_edit",
            args={
                "path": path,
                "old_string": old_string,
                "new_string": new_string,
                "replace_all": replace_all,
            },
            raw_input=raw_input,
        )

    def _parse_git_status(self, match: re.Match, raw_input: str) -> Command:
        """Parse /git status"""
        return Command(tool="git_status", args={}, raw_input=raw_input)

    def _parse_git_diff(self, match: re.Match, raw_input: str) -> Command:
        """Parse /git diff [file]"""
        file_arg = match.group(1).strip() if match.group(1) else None
        args = {"file": file_arg} if file_arg else {}
        return Command(tool="git_diff", args=args, raw_input=raw_input)

    def _parse_git_log(self, match: re.Match, raw_input: str) -> Command:
        """Parse /git log [options]"""
        options = match.group(1).strip() if match.group(1) else ""
        args = {"options": options} if options else {}
        return Command(tool="git_log", args=args, raw_input=raw_input)

    def _parse_git_add(self, match: re.Match, raw_input: str) -> Command:
        """Parse /git add <files>"""
        files = match.group(1).strip()
        return Command(tool="git_add", args={"files": files}, raw_input=raw_input)

    def _parse_git_commit(self, match: re.Match, raw_input: str) -> Command:
        """Parse /git commit <message>"""
        message = match.group(1).strip()
        # Remove quotes if present
        if message.startswith('"') and message.endswith('"'):
            message = message[1:-1]
        elif message.startswith("'") and message.endswith("'"):
            message = message[1:-1]
        return Command(
            tool="git_commit", args={"message": message}, raw_input=raw_input
        )

    def _parse_provider_override(self, match: re.Match, raw_input: str) -> Command:
        """Parse /provider <name>"""
        provider_name = match.group(1).strip().lower()
        return Command(
            tool="provider_override",
            args={"provider": provider_name},
            raw_input=raw_input,
        )

    def get_help_text(self) -> str:
        """Vrátí help text pro dostupné příkazy"""
        return """
Available Commands:

Bash/Terminal:
  /bash <command>        Execute shell command
  /sh <command>          Alias for /bash
  /exec <command>        Alias for /bash

File Operations:
  /file read <path>      Read file contents
  /read <path>           Shortcut for file read
  /file write <path>     Write to file (interactive)
  /write <path>          Shortcut for file write
  /file list [dir]       List files in directory
  /edit <path> "<old>" "<new>" [--all]
                          Edit file content with unique match validation

Git Operations:
  /git status            Show git status
  /git diff [file]       Show git diff
  /git log [options]     Show git log
  /git add <files>       Stage files
  /git commit <msg>      Create commit

Provider Control:
  /provider <name>       Override AI provider selection
                         (claude_anthropic, claude_oauth, gemini,
                          mercury, ollama_local, termux_ollama, ollama_remote)
  /providers             List available providers
Web Tools:
  /web fetch <url> [prompt]
  /web search <query>
"""


# Convenience function
def parse_command(user_input: str) -> Optional[Command]:
    """
    Convenience function pro rychlé parsování příkazu

    Args:
        user_input: Uživatelský vstup

    Returns:
        Command objekt nebo None
    """
    parser = CommandParser()
    return parser.parse(user_input)
