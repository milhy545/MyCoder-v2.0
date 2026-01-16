"""Agent orchestrator for managing multiple agents."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from .base import AgentResult, AgentType, BaseAgent
from .bash import BashAgent
from .explore import ExploreAgent
from .general import GeneralPurposeAgent
from .plan import PlanAgent


class AgentOrchestrator:
    """Orchestrator for selecting and executing agents."""

    def __init__(self, coder, working_directory: Path) -> None:
        self.coder = coder
        self.working_dir = working_directory
        self.agents: Dict[AgentType, BaseAgent] = {
            AgentType.EXPLORE: ExploreAgent(coder, working_directory),
            AgentType.PLAN: PlanAgent(coder, working_directory),
            AgentType.BASH: BashAgent(coder, working_directory),
            AgentType.GENERAL: GeneralPurposeAgent(coder, working_directory),
        }

    def get_agent(self, agent_type: AgentType) -> BaseAgent:
        return self.agents[agent_type]

    def select_agent(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> BaseAgent:
        if context and context.get("agent"):
            requested = str(context["agent"]).lower()
            for agent_type in AgentType:
                if agent_type.value == requested:
                    return self.agents[agent_type]

        lowered = task.lower()
        if lowered.startswith("bash ") or lowered.startswith("bash:"):
            return self.agents[AgentType.BASH]
        if "plan" in lowered or (context and context.get("mode") == "plan"):
            return self.agents[AgentType.PLAN]
        if any(
            keyword in lowered
            for keyword in ("find", "search", "locate", "where is", "grep")
        ):
            return self.agents[AgentType.EXPLORE]
        return self.agents[AgentType.GENERAL]

    async def execute(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        agent = self.select_agent(task, context=context)
        return await agent.execute(task, context=context or {})
