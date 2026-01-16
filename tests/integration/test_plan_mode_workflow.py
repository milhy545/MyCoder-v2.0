import pytest
from pathlib import Path

from mycoder.agents.plan import PlanAgent


class DummyCoder:
    async def process_request(self, prompt: str, **kwargs):
        return {"content": f"plan:{prompt[:20]}"}


@pytest.mark.asyncio
async def test_plan_agent_workflow(tmp_path: Path) -> None:
    agent = PlanAgent(DummyCoder(), tmp_path)

    result = await agent.execute("Do the plan", context={})

    assert result.success is True
    assert result.content.startswith("plan:")
