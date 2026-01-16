"""
Error handling tests for AI simulator.
"""

from __future__ import annotations

import json
from pathlib import Path

from tests.e2e.framework.ai_simulator import SimpleAISimulator


def _load_prompts() -> dict:
    fixture_path = Path(__file__).parent / "fixtures" / "test_prompts.json"
    return json.loads(fixture_path.read_text())


class TestErrorHandling:
    """Validate error-related and ambiguous prompts."""

    def setup_method(self) -> None:
        self.simulator = SimpleAISimulator()
        self.prompts = _load_prompts()["error_handling"]

    def test_error_handling_scenarios(self) -> None:
        for scenario in self.prompts:
            response = self.simulator.simulate(scenario["prompt"])
            assert response["tool"] == scenario["expected_tool"]
            assert response["confidence"] >= scenario.get("confidence_min", 0.0)

    def test_ambiguous_error_prompt(self) -> None:
        ambiguous = next(
            item for item in self.prompts if item["name"] == "ambiguous_error"
        )
        response = self.simulator.simulate(ambiguous["prompt"])
        assert response["tool"] == "ask_user"
        assert response["confidence"] <= 0.6
