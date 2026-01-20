"""
Self-test runner for AI testing framework.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from tests.e2e.framework.ai_simulator import AISimulator, IntelligenceLevel
from tests.e2e.framework.metrics_collector import MetricsCollector
from tests.e2e.framework.report_generator import ReportGenerator
from tests.e2e.framework.scenario_engine import (
    COMMON_SCENARIOS,
    ScenarioEngine,
    ScenarioResult,
    ScenarioType,
)
from tests.e2e.scenarios import (
    context_awareness,
    error_handling,
    prompt_engineering,
    tool_selection,
)


class SelfTestRunner:
    """Autonomous test runner with optional auto-iteration."""

    def __init__(
        self,
        intelligence: IntelligenceLevel = IntelligenceLevel.NORMAL,
        output_dir: Optional[Path] = None,
    ) -> None:
        self.simulator = AISimulator(intelligence_level=intelligence)
        self.engine = ScenarioEngine(self.simulator)
        self.metrics = MetricsCollector()
        self.output_dir = output_dir or Path("tests/e2e/reports")
        self.reporter = ReportGenerator(self.output_dir)

    def run_scenarios(self, scenarios: Iterable[Any]) -> List[ScenarioResult]:
        """Run scenarios and collect metrics."""
        results = []
        for scenario in scenarios:
            result = self.engine.execute_scenario(scenario)
            self._record_metrics(result)
            results.append(result)
        return results

    def _record_metrics(self, result: ScenarioResult) -> None:
        response = result.metadata.get("response", {})
        self.metrics.record_tool_selection(
            expected=result.scenario.expected_tool,
            actual=result.actual_tool,
        )
        self.metrics.record_execution_time(
            result.scenario.name, result.execution_time_ms
        )

        if result.scenario.context:
            self.metrics.record_context_retention(bool(response.get("context_aware")))

        quality_score = response.get("quality_score")
        if quality_score is None:
            quality_score = response.get("confidence", 0.0)
        self.metrics.record_response_quality(float(quality_score))

        if response.get("error"):
            recovered = bool(response.get("recovery_suggestions"))
            self.metrics.record_error_recovery(recovered)
        else:
            self.metrics.record_error_recovery(True)

        self.metrics.record_prompt_adherence(result.passed)

    def auto_iterate(
        self,
        scenarios: Iterable[Any],
        max_iterations: int = 10,
        target_pass_rate: float = 0.95,
    ) -> Dict[str, Any]:
        """Auto-iterate on failures until target pass rate is reached."""
        iteration = 0
        improvements: List[str] = []
        last_results: List[ScenarioResult] = []

        while iteration < max_iterations:
            iteration += 1
            self.engine.reset()
            self.metrics.reset()

            results = self.run_scenarios(scenarios)
            pass_rate = self.engine.get_pass_rate()
            last_results = results

            if pass_rate >= target_pass_rate:
                break

            failures = self.engine.get_failures()
            improvements.extend(self.analyze_failures(failures))

            for improvement in improvements:
                self.apply_improvement(improvement)

        return {
            "iterations": iteration,
            "pass_rate": self.engine.get_pass_rate(),
            "improvements": improvements,
            "results": last_results,
        }

    def analyze_failures(self, failures: Iterable[ScenarioResult]) -> List[str]:
        """Analyze failures and propose improvements."""
        suggestions = []
        for failure in failures:
            suggestions.append(
                f"Review patterns for scenario '{failure.scenario.name}' (expected {failure.scenario.expected_tool})"
            )
        return suggestions

    def apply_improvement(self, improvement: str) -> None:
        """Apply an improvement suggestion (placeholder)."""
        _ = improvement

    def generate_reports(
        self, results: List[ScenarioResult], run_id: str, formats: List[str]
    ) -> Dict[str, Path]:
        """Generate reports in specified formats."""
        metrics = self.metrics.get_metrics()
        report_paths: Dict[str, Path] = {}

        if "console" in formats:
            summary = self.reporter.generate_console_summary(results, metrics)
            print(summary)

        if "json" in formats:
            report_paths["json"] = self.reporter.generate_json_report(
                results, metrics, run_id
            )

        if "html" in formats:
            report_paths["html"] = self.reporter.generate_html_report(
                results, metrics, run_id
            )

        if "md" in formats:
            report_paths["md"] = self.reporter.generate_markdown_report(
                results, metrics, run_id
            )

        return report_paths


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI testing framework runner")
    parser.add_argument(
        "--scenario-type",
        choices=[scenario.value for scenario in ScenarioType],
        help="Filter scenarios by type",
    )
    parser.add_argument(
        "--auto-iterate",
        action="store_true",
        help="Enable auto-iteration on failures",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="Maximum iterations for auto-iteration",
    )
    parser.add_argument(
        "--target-pass-rate",
        type=float,
        default=0.95,
        help="Target pass rate for auto-iteration",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate reports",
    )
    parser.add_argument(
        "--report-formats",
        default="console,json",
        help="Comma-separated report formats: console,json,html,md",
    )
    parser.add_argument(
        "--intelligence",
        choices=[level.value for level in IntelligenceLevel],
        default=IntelligenceLevel.NORMAL.value,
        help="Intelligence level for simulator",
    )
    parser.add_argument(
        "--source",
        choices=["fixtures", "common"],
        default="fixtures",
        help="Scenario source (fixtures or common)",
    )
    return parser.parse_args()


def _filter_scenarios(scenario_type: Optional[str], source: str) -> List[Any]:
    if source == "common":
        if not scenario_type:
            return list(COMMON_SCENARIOS)
        return [
            scenario
            for scenario in COMMON_SCENARIOS
            if scenario.type.value == scenario_type
        ]

    return _load_fixture_scenarios(scenario_type)


def _load_fixture_scenarios(scenario_type: Optional[str]) -> List[Any]:
    modules = {
        ScenarioType.PROMPT_ENGINEERING.value: prompt_engineering.get_scenarios,
        ScenarioType.TOOL_SELECTION.value: tool_selection.get_scenarios,
        ScenarioType.CONTEXT_AWARENESS.value: context_awareness.get_scenarios,
        ScenarioType.ERROR_HANDLING.value: error_handling.get_scenarios,
    }

    if scenario_type:
        loader = modules.get(scenario_type)
        return loader() if loader else []

    scenarios: List[Any] = []
    for loader in modules.values():
        scenarios.extend(loader())
    return scenarios


def main() -> None:
    args = _parse_args()
    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    intelligence = IntelligenceLevel(args.intelligence)

    scenarios = _filter_scenarios(args.scenario_type, args.source)
    runner = SelfTestRunner(intelligence=intelligence)

    if args.auto_iterate:
        summary = runner.auto_iterate(
            scenarios,
            max_iterations=args.max_iterations,
            target_pass_rate=args.target_pass_rate,
        )
        results = summary["results"]
    else:
        results = runner.run_scenarios(scenarios)

    if args.report:
        formats = [fmt.strip() for fmt in args.report_formats.split(",") if fmt.strip()]
        runner.generate_reports(results, run_id, formats)


if __name__ == "__main__":
    main()
