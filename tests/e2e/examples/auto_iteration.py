"""Auto-iteration example for the AI testing runner."""

from __future__ import annotations

from tests.e2e.runner import SelfTestRunner
from tests.e2e.scenarios.fixture_loader import load_scenarios


def main() -> None:
    runner = SelfTestRunner()
    scenarios = load_scenarios()

    summary = runner.auto_iterate(scenarios, max_iterations=5, target_pass_rate=0.95)
    print(f"Iterations: {summary['iterations']}")
    print(f"Pass rate: {summary['pass_rate'] * 100:.1f}%")
    print(f"Improvements: {summary['improvements']}")


if __name__ == "__main__":
    main()
