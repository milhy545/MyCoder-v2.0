"""
Tool selection tests for AI simulator.
"""

from __future__ import annotations

import json
from pathlib import Path

from tests.e2e.framework.ai_simulator import SimpleAISimulator
from tests.e2e.framework.scenario_engine import (
    ScenarioDefinition,
    ScenarioEngine,
    ScenarioType,
)


def _load_prompts() -> dict:
    fixture_path = Path(__file__).parent / "fixtures" / "test_prompts.json"
    return json.loads(fixture_path.read_text())


class TestToolSelection:
    """Validate tool selection accuracy for common tasks."""

    def setup_method(self) -> None:
        self.simulator = SimpleAISimulator()
        self.engine = ScenarioEngine(self.simulator)
        self.prompts = _load_prompts()["tool_selection"]

    def test_tool_selection_scenarios(self) -> None:
        scenarios = [
            ScenarioDefinition(
                name=item["name"],
                type=ScenarioType.TOOL_SELECTION,
                user_input=item["prompt"],
                expected_tool=item["expected_tool"],
                expected_confidence=item.get("confidence_min", 0.7),
            )
            for item in self.prompts
        ]

        results = self.engine.execute_suite(scenarios)
        assert all(result.passed for result in results)

    def test_tool_selection_pass_rate(self) -> None:
        scenarios = [
            ScenarioDefinition(
                name=item["name"],
                type=ScenarioType.TOOL_SELECTION,
                user_input=item["prompt"],
                expected_tool=item["expected_tool"],
                expected_confidence=item.get("confidence_min", 0.7),
            )
            for item in self.prompts
        ]

        self.engine.execute_suite(scenarios)
        assert self.engine.get_pass_rate() >= 0.9
