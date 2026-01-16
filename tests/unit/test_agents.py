from pathlib import Path

import pytest

from mycoder.agents.base import AgentType
from mycoder.agents.bash import BashAgent
from mycoder.agents.explore import ExploreAgent
from mycoder.agents.general import GeneralPurposeAgent
from mycoder.agents.orchestrator import AgentOrchestrator
from mycoder.agents.plan import PlanAgent


class DummyCoder:
    def __init__(self) -> None:
        self.calls = []

    async def process_request(self, prompt: str, **kwargs):
        self.calls.append((prompt, kwargs))
        return {"content": f"response:{prompt}"}


@pytest.mark.asyncio
async def test_plan_agent_uses_coder(tmp_path: Path) -> None:
    coder = DummyCoder()
    agent = PlanAgent(coder, tmp_path)

    result = await agent.execute("Plan this", context={})

    assert result.success is True
    assert "response:" in result.content
    assert coder.calls


@pytest.mark.asyncio
async def test_general_agent_uses_coder(tmp_path: Path) -> None:
    coder = DummyCoder()
    agent = GeneralPurposeAgent(coder, tmp_path)

    result = await agent.execute("Hello", context={})

    assert result.success is True
    assert result.agent_type == AgentType.GENERAL
    assert coder.calls


@pytest.mark.asyncio
async def test_bash_agent_runs_command(tmp_path: Path) -> None:
    agent = BashAgent(DummyCoder(), tmp_path)

    result = await agent.execute("echo test")

    assert result.success is True
    assert result.content.strip() == "test"


@pytest.mark.asyncio
async def test_explore_agent_lists_structure(tmp_path: Path) -> None:
    (tmp_path / "alpha.txt").write_text("data", encoding="utf-8")
    agent = ExploreAgent(DummyCoder(), tmp_path)

    result = await agent.execute("show structure")

    assert result.success is True
    assert "alpha.txt" in result.content


@pytest.mark.asyncio
async def test_orchestrator_selects_agent(tmp_path: Path) -> None:
    coder = DummyCoder()
    orchestrator = AgentOrchestrator(coder, tmp_path)

    agent = orchestrator.select_agent("find file *.py", context={})

    assert agent.agent_type == AgentType.EXPLORE
