"""Basic usage example for the AI testing runner."""

from __future__ import annotations

from tests.e2e.framework.ai_simulator import AISimulator, IntelligenceLevel
from tests.e2e.framework.scenario_engine import ScenarioEngine
from tests.e2e.scenarios.fixture_loader import load_scenarios


def main() -> None:
    simulator = AISimulator(intelligence_level=IntelligenceLevel.NORMAL)
    engine = ScenarioEngine(simulator)
    scenarios = load_scenarios()

    results = engine.execute_suite(scenarios)
    pass_rate = engine.get_pass_rate()
    failures = engine.get_failures()

    print(f"Scenarios executed: {len(results)}")
    print(f"Pass rate: {pass_rate * 100:.1f}%")
    if failures:
        print("Failures:")
        for result in failures:
            print(f"- {result.scenario.name}: {', '.join(result.failures)}")


if __name__ == "__main__":
    main()
