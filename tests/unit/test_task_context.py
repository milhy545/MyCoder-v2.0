"""Unit tests for TaskContext."""

from mycoder.router.task_context import ModelRole, TaskContext


class TestTaskContext:
    """Tests for TaskContext."""

    def test_add_execution_tracks_cost(self):
        ctx = TaskContext(original_prompt="test", budget_remaining_usd=10.0)

        ctx.add_execution(
            role=ModelRole.WORKER,
            model_name="gpt-4o",
            prompt="test prompt",
            response="test response",
            cost_usd=0.05,
            duration_ms=500,
        )

        assert ctx.cost_so_far_usd == 0.05
        assert ctx.budget_remaining_usd == 9.95
        assert len(ctx.execution_history) == 1

    def test_summary(self):
        ctx = TaskContext(original_prompt="test summary")
        ctx.generated_code["file.py"] = "code"
        summary = ctx.get_summary()

        assert summary["original_prompt"] == "test summary"
        assert summary["files_modified"] == ["file.py"]
