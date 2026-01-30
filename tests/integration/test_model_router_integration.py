"""Integration tests for ModelRouter."""

from unittest.mock import AsyncMock

import pytest

from mycoder.router.adapters.base import AdapterResponse
from mycoder.router.model_router import ModelRouter
from mycoder.router.task_context import BudgetTier, ModelRole


class TestModelRouterIntegration:
    """Integration tests for ModelRouter."""

    @pytest.fixture
    def mock_adapters(self):
        claude = AsyncMock()
        claude.model_info.name = "claude-opus-4-20250514"
        claude.query.return_value = AdapterResponse(
            success=True,
            content="Plan: 1. Do it.",
            model_name="claude-opus-4-20250514",
            input_tokens=10,
            output_tokens=10,
            cost_usd=0.1,
            duration_ms=1000,
        )

        gpt4o = AsyncMock()
        gpt4o.model_info.name = "gpt-4o"
        gpt4o.query.return_value = AdapterResponse(
            success=True,
            content="print('Hello')",
            model_name="gpt-4o",
            input_tokens=10,
            output_tokens=10,
            cost_usd=0.01,
            duration_ms=500,
        )

        gemini = AsyncMock()
        gemini.model_info.name = "gemini-2.0-flash"
        gemini.query.return_value = AdapterResponse(
            success=True,
            content="LGTM",
            model_name="gemini-2.0-flash",
            input_tokens=100,
            output_tokens=5,
            cost_usd=0.001,
            duration_ms=200,
        )

        return {"claude": claude, "gpt4o": gpt4o, "gemini": gemini}

    @pytest.mark.asyncio
    async def test_full_orchestration_flow(self, mock_adapters):
        """Test the full Architect -> Worker -> Reviewer flow."""
        router = ModelRouter(default_budget=BudgetTier.UNLIMITED)

        # Inject mocks manually
        router.adapters["claude-opus-4-20250514"] = mock_adapters["claude"]
        router.adapters["gpt-4o"] = mock_adapters["gpt4o"]
        router.adapters["gemini-2.0-flash"] = mock_adapters["gemini"]

        # Setup responses for the sequence
        # 1. Architect returns a plan
        mock_adapters["claude"].query.return_value = AdapterResponse(
            success=True,
            content="## Implementation Plan\n1. Step 1: Implement feature.\n2. Step 2: Verify.",
            model_name="claude-opus-4-20250514",
            input_tokens=50,
            output_tokens=50,
            cost_usd=0.5,
            duration_ms=1000,
        )

        # 2. Worker implements code
        mock_adapters["gpt4o"].query.return_value = AdapterResponse(
            success=True,
            content="def feature():\n    return True",
            model_name="gpt-4o",
            input_tokens=100,
            output_tokens=20,
            cost_usd=0.05,
            duration_ms=500,
        )

        # 3. Reviewer reviews code
        mock_adapters["gemini"].query.return_value = AdapterResponse(
            success=True,
            content="LGTM. The code is correct.",
            model_name="gemini-2.0-flash",
            input_tokens=150,
            output_tokens=10,
            cost_usd=0.001,
            duration_ms=200,
        )

        # Run orchestration
        # We start with a COMPLEX task that needs Architect
        result = await router.orchestrate_full_task(
            prompt="Architect and implement a complex feature.",
            budget=BudgetTier.UNLIMITED,
            max_handoffs=3,
        )

        # Assertions
        assert result.success
        assert result.task_context.cost_so_far_usd > 0

        # Check execution history
        history = result.task_context.execution_history
        assert len(history) == 3
        assert history[0]["role"] == ModelRole.ARCHITECT.value
        assert history[1]["role"] == ModelRole.WORKER.value
        assert history[2]["role"] == ModelRole.REVIEWER.value

        assert result.task_context.review_passed is True

    @pytest.mark.asyncio
    async def test_simple_task_no_handoff(self, mock_adapters):
        router = ModelRouter(default_budget=BudgetTier.STANDARD)
        router.adapters["gpt-4o"] = mock_adapters["gpt4o"]

        # Simple task
        mock_adapters["gpt4o"].query.return_value = AdapterResponse(
            success=True,
            content="Fixed typo.",
            model_name="gpt-4o",
            input_tokens=10,
            output_tokens=5,
            cost_usd=0.01,
            duration_ms=100,
        )

        result = await router.orchestrate_full_task(
            prompt="Fix typo in README", budget=BudgetTier.STANDARD
        )

        assert result.success
        assert len(result.task_context.execution_history) == 1
        assert (
            result.task_context.execution_history[0]["role"] == ModelRole.WORKER.value
        )  # Typo fix is TRIVIAL -> WORKER (mapped to Worker in router)
