import pytest
from pathlib import Path

from mycoder.agents.orchestrator import AgentOrchestrator
from mycoder.agents.base import AgentType


class DummyCoder:
    async def process_request(self, prompt: str, **kwargs):
        return {"content": f"response:{prompt}"}


@pytest.mark.asyncio
async def test_orchestrator_execute_routes(tmp_path: Path) -> None:
    orchestrator = AgentOrchestrator(DummyCoder(), tmp_path)

    result = await orchestrator.execute("find file *.py", context={})

    assert result.agent_type == AgentType.EXPLORE
