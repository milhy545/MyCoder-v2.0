"""Agent for executing shell commands."""

from __future__ import annotations

import subprocess
from typing import Any, Dict

from .base import BaseAgent, AgentResult, AgentType


class BashAgent(BaseAgent):
    """Agent for running bash commands."""

    @property
    def agent_type(self) -> AgentType:
        return AgentType.BASH

    @property
    def description(self) -> str:
        return "Execute shell commands and return output"

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AgentResult:
        command = task.strip()
        if not command:
            return AgentResult(
                success=False,
                content="No command provided.",
                agent_type=self.agent_type,
                error="Command is empty",
            )

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except Exception as exc:
            return AgentResult(
                success=False,
                content="",
                agent_type=self.agent_type,
                error=str(exc),
            )

        output = result.stdout.strip()
        if not output and result.stderr:
            output = result.stderr.strip()

        return AgentResult(
            success=result.returncode == 0,
            content=output or "",
            agent_type=self.agent_type,
            metadata={"returncode": result.returncode},
            error=None if result.returncode == 0 else output or "Command failed",
        )
