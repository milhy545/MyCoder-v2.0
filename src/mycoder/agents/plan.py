"""Software architect agent for designing implementation plans."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .base import AgentResult, AgentType, BaseAgent


@dataclass
class PlanStep:
    step_number: int
    description: str
    files_affected: List[str]
    estimated_complexity: str


@dataclass
class ImplementationPlan:
    summary: str
    steps: List[PlanStep]
    critical_files: List[str]
    risks: List[str]
    dependencies: List[str]


class PlanAgent(BaseAgent):
    """Agent for implementation planning."""

    @property
    def agent_type(self) -> AgentType:
        return AgentType.PLAN

    @property
    def description(self) -> str:
        return (
            "Design implementation plans, identify critical files, consider trade-offs"
        )

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AgentResult:
        plan_prompt = self._build_plan_prompt(task, context)

        response = await self.coder.process_request(plan_prompt, use_tools=False)
        content = (
            response.get("content") if isinstance(response, dict) else str(response)
        )

        return AgentResult(
            success=True,
            content=content,
            agent_type=self.agent_type,
            metadata={"task": task},
        )

    def _build_plan_prompt(self, task: str, context: Dict[str, Any] = None) -> str:
        return (
            "You are a software architect. Create an implementation plan for:\n\n"
            f"Task: {task}\n\n"
            f"Project context:\n- Working directory: {self.working_dir}\n"
            "- Language: Python 3.10+\n"
            "- Framework: MyCoder AI assistant\n\n"
            "Provide:\n"
            "1. Summary of approach\n"
            "2. Step-by-step implementation (no time estimates)\n"
            "3. Critical files to modify\n"
            "4. Potential risks\n"
            "5. Dependencies to add (if any)\n\n"
            "Format as structured markdown."
        )
