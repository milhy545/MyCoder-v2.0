"""Custom scenario example for the AI testing framework."""

from __future__ import annotations

from tests.e2e.framework.ai_simulator import AISimulator, IntelligenceLevel
from tests.e2e.framework.scenario_engine import (
    ScenarioDefinition,
    ScenarioEngine,
    ScenarioType,
)


def main() -> None:
    simulator = AISimulator(intelligence_level=IntelligenceLevel.HIGH)
    engine = ScenarioEngine(simulator)

    scenarios = [
        ScenarioDefinition(
            name="custom_file_read",
            type=ScenarioType.TOOL_SELECTION,
            user_input="Read README.md",
            expected_tool="file_read",
            expected_confidence=0.8,
        ),
        ScenarioDefinition(
            name="custom_multi_step",
            type=ScenarioType.MULTI_STEP,
            user_input="Read README.md and run tests",
            expected_tool="multi_step",
            expected_confidence=0.7,
        ),
    ]

    results = engine.execute_suite(scenarios)
    for result in results:
        print(f"{result.scenario.name}: {'PASS' if result.passed else 'FAIL'}")


if __name__ == "__main__":
    main()
