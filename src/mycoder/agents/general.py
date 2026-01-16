"""General-purpose agent for open-ended tasks."""

from __future__ import annotations

from typing import Any, Dict

from .base import AgentResult, AgentType, BaseAgent


class GeneralPurposeAgent(BaseAgent):
    """Agent for general queries and tasks."""

    @property
    def agent_type(self) -> AgentType:
        return AgentType.GENERAL

    @property
    def description(self) -> str:
        return "General-purpose agent for analysis, coding, and guidance"

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AgentResult:
        response = await self.coder.process_request(task)
        content = (
            response.get("content") if isinstance(response, dict) else str(response)
        )

        return AgentResult(
            success=True,
            content=content,
            agent_type=self.agent_type,
            metadata={"task": task},
        )
