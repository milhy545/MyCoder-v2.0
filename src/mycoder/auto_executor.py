import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple


class ActionType(Enum):
    CREATE_FILE = "create_file"
    EDIT_FILE = "edit_file"
    RUN_COMMAND = "run_command"
    INSTALL_PACKAGE = "install_package"


@dataclass
class ProposedAction:
    type: ActionType
    target: str
    content: Optional[str] = None
    description: str = ""
    confidence: float = 0.0


class AIResponseParser:
    """Parse AI responses to extract proposed actions."""

    FILE_CREATE_PATTERNS = [
        r"```(?:python|javascript|typescript|bash|sh|json|yaml|toml|md)\n# (?:File: )?([^\n]+)\n([\s\S]*?)```",
        r"(?:vytvoř|create|write)(?: soubor| file)?\s+[`']?([^`'\n]+)[`']?",
        r"# ([a-zA-Z_/]+\.[a-z]+)\n```[\s\S]*?```",
    ]

    COMMAND_PATTERNS = [
        r"```(?:bash|sh|shell)\n([\s\S]*?)```",
        r"spusť[:\s]+`([^`]+)`",
        r"run[:\s]+`([^`]+)`",
    ]

    def parse(self, response: str) -> List[ProposedAction]:
        """Extract all proposed actions from AI response."""
        actions: List[ProposedAction] = []
        actions.extend(self._find_file_creates(response))
        actions.extend(self._find_commands(response))
        actions.extend(self._find_installs(response))
        return actions

    def _find_file_creates(self, text: str) -> List[ProposedAction]:
        actions: List[ProposedAction] = []
        patterns = [
            (r"```(?:\w+)?\n\s*#\s*(?:File:\s*)?([^\n]+)\n([\s\S]*?)```", 0),
            (r"```(?:\w+)?\n\s*//\s*(?:File:\s*)?([^\n]+)\n([\s\S]*?)```", 0),
            (
                r"(?:file|soubor):\s*([^\n]+)\n```(?:\w+)?\n([\s\S]*?)```",
                re.IGNORECASE,
            ),
        ]
        for pattern, flags in patterns:
            for match in re.finditer(pattern, text, flags):
                filename, content = match.groups()
                filename = filename.strip()
                content = content.strip()
                if not content:
                    continue
                if (
                    "/" in filename
                    or "\\" in filename
                    or filename.endswith(
                        (".py", ".js", ".ts", ".json", ".md", ".yaml", ".yml", ".toml")
                    )
                ):
                    actions.append(
                        ProposedAction(
                            type=ActionType.CREATE_FILE,
                            target=filename,
                            content=content,
                            description=f"Create {filename}",
                            confidence=0.9,
                        )
                    )
        return actions

    def _find_commands(self, text: str) -> List[ProposedAction]:
        actions: List[ProposedAction] = []
        pattern = r"```(?:bash|sh|shell)\n([\s\S]*?)```"
        for match in re.finditer(pattern, text):
            commands = match.group(1).strip().split("\n")
            for cmd in commands:
                cmd = cmd.strip()
                if cmd and not cmd.startswith("#"):
                    if self._is_safe_command(cmd):
                        actions.append(
                            ProposedAction(
                                type=ActionType.RUN_COMMAND,
                                target=cmd,
                                description=f"Run: {cmd[:50]}",
                                confidence=0.7,
                            )
                        )
        return actions

    def _find_installs(self, text: str) -> List[ProposedAction]:
        actions: List[ProposedAction] = []
        patterns = [
            ("pip install", r"pip install\s+([^\n`]+)"),
            ("poetry add", r"poetry add\s+([^\n`]+)"),
            ("npm install", r"npm install\s+([^\n`]+)"),
        ]

        for prefix, pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                pkg = match.group(1).strip()
                actions.append(
                    ProposedAction(
                        type=ActionType.INSTALL_PACKAGE,
                        target=f"{prefix} {pkg}",
                        description=f"Install: {pkg}",
                        confidence=0.8,
                    )
                )

        return actions

    def _is_safe_command(self, cmd: str) -> bool:
        """Check if command is safe to auto-execute."""
        dangerous = [
            "rm -rf",
            "sudo rm",
            "mkfs",
            "dd if=",
            "> /dev/",
            "chmod 777",
            "curl | bash",
        ]
        cmd_lower = cmd.lower()
        return not any(d in cmd_lower for d in dangerous)


class AutoExecutor:
    """Execute proposed actions with user confirmation."""

    def __init__(self, activity_panel=None, require_confirmation: bool = True):
        self.parser = AIResponseParser()
        self.activity_panel = activity_panel
        self.require_confirmation = require_confirmation
        self.executed_actions: List[ProposedAction] = []

    async def process_response(
        self,
        response: str,
        confirm_callback=None,
        execute_callback=None,
    ) -> List[Tuple[ProposedAction, bool]]:
        """
        Process AI response, extract actions, confirm with user, execute.

        Returns list of (action, success) tuples.
        """
        actions = self.parser.parse(response)
        results: List[Tuple[ProposedAction, bool]] = []

        for action in actions:
            if action.confidence < 0.5:
                continue

            should_execute = True
            if self.require_confirmation and confirm_callback:
                should_execute = await confirm_callback(action)

            if not should_execute:
                results.append((action, False))
                continue

            success = False
            if execute_callback:
                try:
                    success = await execute_callback(action)
                except Exception:
                    success = False

            results.append((action, success))

            if success:
                self.executed_actions.append(action)
                if self.activity_panel:
                    from .ui_activity_panel import Activity, ActivityType

                    act_type = {
                        ActionType.CREATE_FILE: ActivityType.FILE_CREATE,
                        ActionType.EDIT_FILE: ActivityType.FILE_EDIT,
                        ActionType.RUN_COMMAND: ActivityType.BASH_EXEC,
                        ActionType.INSTALL_PACKAGE: ActivityType.BASH_EXEC,
                    }.get(action.type, ActivityType.TOOL_CALL)

                    self.activity_panel.add_activity(
                        Activity(
                            type=act_type,
                            description=action.description,
                            target=action.target,
                            status="done",
                        )
                    )

        return results
