"""
Metrics collection for AI testing framework.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ExecutionRecord:
    """Execution timing record."""

    scenario_name: str
    time_ms: int


@dataclass
class MetricsCollector:
    """Collects and aggregates AI testing metrics."""

    tool_selections: List[bool] = field(default_factory=list)
    context_retention: List[bool] = field(default_factory=list)
    response_quality_scores: List[float] = field(default_factory=list)
    error_recovery: List[bool] = field(default_factory=list)
    prompt_adherence: List[bool] = field(default_factory=list)
    execution_times: List[ExecutionRecord] = field(default_factory=list)

    def record_tool_selection(
        self, expected: str, actual: str, correct: Optional[bool] = None
    ) -> None:
        """Record tool selection correctness."""
        is_correct = correct if correct is not None else expected == actual
        self.tool_selections.append(is_correct)

    def record_context_retention(self, retained: bool) -> None:
        """Record context retention outcome."""
        self.context_retention.append(retained)

    def record_response_quality(self, score: float) -> None:
        """Record response quality score (0-1)."""
        self.response_quality_scores.append(score)

    def record_error_recovery(self, recovered: bool) -> None:
        """Record error recovery outcome."""
        self.error_recovery.append(recovered)

    def record_prompt_adherence(self, adhered: bool) -> None:
        """Record prompt adherence outcome."""
        self.prompt_adherence.append(adhered)

    def record_execution_time(self, scenario_name: str, time_ms: int) -> None:
        """Record scenario execution time in milliseconds."""
        self.execution_times.append(ExecutionRecord(scenario_name, time_ms))

    def get_metrics(self) -> Dict[str, float]:
        """Return aggregated metrics."""
        return {
            "tool_accuracy": self._rate(self.tool_selections),
            "context_retention": self._rate(self.context_retention),
            "response_quality": self._average(self.response_quality_scores),
            "error_recovery": self._rate(self.error_recovery),
            "prompt_adherence": self._rate(self.prompt_adherence),
            "avg_execution_time_ms": self._average_times(),
        }

    def get_execution_time(self, scenario_name: str) -> Optional[int]:
        """Return the most recent execution time for a scenario."""
        for record in reversed(self.execution_times):
            if record.scenario_name == scenario_name:
                return record.time_ms
        return None

    def reset(self) -> None:
        """Reset all metrics."""
        self.tool_selections.clear()
        self.context_retention.clear()
        self.response_quality_scores.clear()
        self.error_recovery.clear()
        self.prompt_adherence.clear()
        self.execution_times.clear()

    @staticmethod
    def _rate(values: List[bool]) -> float:
        if not values:
            return 0.0
        return sum(1 for value in values if value) / len(values)

    @staticmethod
    def _average(values: List[float]) -> float:
        if not values:
            return 0.0
        return sum(values) / len(values)

    def _average_times(self) -> float:
        if not self.execution_times:
            return 0.0
        return sum(record.time_ms for record in self.execution_times) / len(
            self.execution_times
        )
