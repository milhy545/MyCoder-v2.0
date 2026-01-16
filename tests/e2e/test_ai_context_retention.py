"""
Context awareness tests for AI simulator.
"""

from __future__ import annotations

import json
from pathlib import Path

from tests.e2e.framework.ai_simulator import AISimulator, IntelligenceLevel


def _load_prompts() -> dict:
    fixture_path = Path(__file__).parent / "fixtures" / "test_prompts.json"
    return json.loads(fixture_path.read_text())


class TestContextRetention:
    """Validate context awareness behavior."""

    def setup_method(self) -> None:
        self.simulator = AISimulator(intelligence_level=IntelligenceLevel.HIGH)
        self.prompts = _load_prompts()["context_awareness"]

    def test_context_awareness_scenarios(self) -> None:
        for scenario in self.prompts:
            response = self.simulator.simulate(
                scenario["prompt"], context=scenario.get("context")
            )
            assert response["tool"] == scenario["expected_tool"]
            assert response.get("context_aware") is True

    def test_context_awareness_confidence(self) -> None:
        scenario = self.prompts[0]
        response = self.simulator.simulate(
            scenario["prompt"], context=scenario.get("context")
        )
        assert response["confidence"] >= scenario.get("confidence_min", 0.7)
