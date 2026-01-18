"""Unit tests for ModelRouter."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from mycoder.router.model_router import ModelRouter
from mycoder.router.task_context import (
    BudgetTier,
    ModelRole,
    TaskComplexity,
    TaskContext,
)


class TestModelRouter:
    """Tests for ModelRouter."""

    @pytest.fixture
    def router(self):
        return ModelRouter(default_budget=BudgetTier.STANDARD)

    def test_complexity_role_mapping(self, router):
        assert router.COMPLEXITY_ROLE_MAP[TaskComplexity.COMPLEX] == ModelRole.ARCHITECT
        assert router.COMPLEXITY_ROLE_MAP[TaskComplexity.SIMPLE] == ModelRole.WORKER
        assert router.COMPLEXITY_ROLE_MAP[TaskComplexity.REVIEW] == ModelRole.REVIEWER

    @pytest.mark.asyncio
    async def test_select_adapter_fallback(self, router):
        # Mock only a cheap adapter
        mock_adapter = AsyncMock()
        mock_adapter.model_info = MagicMock(name="gpt-4o-mini")
        mock_adapter.query.return_value = MagicMock(
            success=True, content="ok", cost_usd=0.01, duration_ms=100
        )

        # We need to manually populate router.adapters because logic uses BUDGET_MODEL_MAP
        # to look up names, then checks self.adapters.
        # Let's say we have GPT-4o-mini (Worker, Minimal/Low) but NOT GPT-4o (Worker, Standard).

        router.adapters["gpt-4o-mini"] = mock_adapter

        # Request STANDARD budget for WORKER (Should be GPT-4o)
        # But GPT-4o is not in adapters.
        # Should fall back to GPT-4o-mini (LOW/MINIMAL).

        adapter = router._select_adapter(
            role=ModelRole.WORKER,
            budget=BudgetTier.STANDARD,
            context=TaskContext(original_prompt="test"),
        )

        assert adapter is not None
        assert adapter == mock_adapter

    @pytest.mark.asyncio
    async def test_handoff_architect_to_worker(self, router):
        # Simulate Architect response with a plan
        ctx = TaskContext(original_prompt="Build a website")

        response = MagicMock()
        response.content = "I have a plan: Step 1. Implement HTML. Step 2. CSS."

        requires_handoff, next_role, handoff_prompt = router._check_handoff(
            current_role=ModelRole.ARCHITECT,
            response=response,
            context=ctx,
            classification=MagicMock(complexity=TaskComplexity.COMPLEX),
        )

        assert requires_handoff is True
        assert next_role == ModelRole.WORKER
        assert "Implement the plan" in handoff_prompt
        assert ctx.plan == response.content

    @pytest.mark.asyncio
    async def test_handoff_worker_to_reviewer(self, router):
        # Simulate Worker response with code
        ctx = TaskContext(original_prompt="Fix bug")

        response = MagicMock()
        response.content = "def fix(): pass"

        requires_handoff, next_role, handoff_prompt = router._check_handoff(
            current_role=ModelRole.WORKER,
            response=response,
            context=ctx,
            classification=MagicMock(complexity=TaskComplexity.COMPLEX),
        )

        assert requires_handoff is True
        assert next_role == ModelRole.REVIEWER
        assert "Review the code" in handoff_prompt
