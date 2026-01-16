"""
Report generation for AI testing framework.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


class ReportGenerator:
    """Generates console, JSON, HTML, and Markdown reports."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_console_summary(
        self,
        results: Iterable[Any],
        metrics: Dict[str, float],
    ) -> str:
        """Create a console-friendly summary string."""
        results_list = list(results)
        total = len(results_list)
        passed = sum(1 for result in results_list if result.passed)
        failed = total - passed
        pass_rate = (passed / total) if total else 0.0

        lines = [
            "AI Testing Framework - Test Run",
            "=" * 34,
            "",
            f"Scenarios Executed: {total}",
            f"Passed: {passed} ({pass_rate * 100:.1f}%)",
            f"Failed: {failed} ({(failed / total * 100) if total else 0:.1f}%)",
            "",
            "Metrics:",
            f"  Tool Accuracy: {metrics.get('tool_accuracy', 0.0) * 100:.1f}%",
            f"  Context Retention: {metrics.get('context_retention', 0.0) * 100:.1f}%",
            f"  Avg Response Time: {metrics.get('avg_execution_time_ms', 0.0):.0f}ms",
        ]

        if failed:
            lines.append("")
            lines.append("Failed Scenarios:")
            for index, result in enumerate(
                [result for result in results_list if not result.passed], start=1
            ):
                failure_reason = (
                    "; ".join(result.failures) if result.failures else "Unknown"
                )
                lines.append(f"  {index}. {result.scenario.name} - {failure_reason}")

        return "\n".join(lines)

    def generate_json_report(
        self,
        results: Iterable[Any],
        metrics: Dict[str, float],
        run_id: str,
    ) -> Path:
        """Write JSON report and return its path."""
        results_list = list(results)
        report = {
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat(),
            "total_scenarios": len(results_list),
            "passed": sum(1 for result in results_list if result.passed),
            "failed": sum(1 for result in results_list if not result.passed),
            "pass_rate": self._pass_rate(results_list),
            "metrics": metrics,
            "failures": [
                {
                    "scenario": result.scenario.name,
                    "expected_tool": result.scenario.expected_tool,
                    "actual_tool": result.actual_tool,
                    "failures": result.failures,
                }
                for result in results_list
                if not result.passed
            ],
        }

        path = self.output_dir / f"run_{run_id}.json"
        path.write_text(json.dumps(report, indent=2))
        return path

    def generate_markdown_report(
        self,
        results: Iterable[Any],
        metrics: Dict[str, float],
        run_id: str,
    ) -> Path:
        """Write Markdown report and return its path."""
        results_list = list(results)
        total = len(results_list)
        passed = sum(1 for result in results_list if result.passed)
        failed = total - passed
        pass_rate = self._pass_rate(results_list)

        lines = [
            f"# AI Testing Framework Report ({run_id})",
            "",
            f"- Scenarios executed: {total}",
            f"- Passed: {passed}",
            f"- Failed: {failed}",
            f"- Pass rate: {pass_rate * 100:.1f}%",
            "",
            "## Metrics",
            "",
            f"- Tool accuracy: {metrics.get('tool_accuracy', 0.0) * 100:.1f}%",
            f"- Context retention: {metrics.get('context_retention', 0.0) * 100:.1f}%",
            f"- Response quality: {metrics.get('response_quality', 0.0):.2f}",
            f"- Error recovery: {metrics.get('error_recovery', 0.0) * 100:.1f}%",
            f"- Prompt adherence: {metrics.get('prompt_adherence', 0.0) * 100:.1f}%",
            f"- Avg execution time: {metrics.get('avg_execution_time_ms', 0.0):.0f}ms",
        ]

        if failed:
            lines.extend(["", "## Failures", ""])
            for result in results_list:
                if not result.passed:
                    lines.append(
                        f"- {result.scenario.name}: {', '.join(result.failures) or 'Unknown'}"
                    )

        path = self.output_dir / f"run_{run_id}.md"
        path.write_text("\n".join(lines))
        return path

    def generate_html_report(
        self,
        results: Iterable[Any],
        metrics: Dict[str, float],
        run_id: str,
    ) -> Path:
        """Write HTML report and return its path."""
        results_list = list(results)
        total = len(results_list)
        passed = sum(1 for result in results_list if result.passed)
        failed = total - passed
        pass_rate = self._pass_rate(results_list)

        failures_html = "".join(
            f"<li>{result.scenario.name}: {'; '.join(result.failures) or 'Unknown'}</li>"
            for result in results_list
            if not result.passed
        )

        html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <title>AI Testing Framework Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    .summary {{ margin-bottom: 24px; }}
    .metric {{ margin: 4px 0; }}
  </style>
</head>
<body>
  <h1>AI Testing Framework Report ({run_id})</h1>
  <div class=\"summary\">
    <p>Scenarios executed: {total}</p>
    <p>Passed: {passed}</p>
    <p>Failed: {failed}</p>
    <p>Pass rate: {pass_rate * 100:.1f}%</p>
  </div>
  <h2>Metrics</h2>
  <div class=\"metric\">Tool accuracy: {metrics.get('tool_accuracy', 0.0) * 100:.1f}%</div>
  <div class=\"metric\">Context retention: {metrics.get('context_retention', 0.0) * 100:.1f}%</div>
  <div class=\"metric\">Response quality: {metrics.get('response_quality', 0.0):.2f}</div>
  <div class=\"metric\">Error recovery: {metrics.get('error_recovery', 0.0) * 100:.1f}%</div>
  <div class=\"metric\">Prompt adherence: {metrics.get('prompt_adherence', 0.0) * 100:.1f}%</div>
  <div class=\"metric\">Avg execution time: {metrics.get('avg_execution_time_ms', 0.0):.0f}ms</div>
  <h2>Failures</h2>
  <ul>
    {failures_html or '<li>None</li>'}
  </ul>
</body>
</html>
"""

        path = self.output_dir / f"run_{run_id}.html"
        path.write_text(html)
        return path

    @staticmethod
    def _pass_rate(results_list: List[Any]) -> float:
        if not results_list:
            return 0.0
        passed = sum(1 for result in results_list if result.passed)
        return passed / len(results_list)

    @staticmethod
    def serialize_results(results: Iterable[Any]) -> List[Dict[str, Any]]:
        """Serialize ScenarioResult objects for external use."""
        serialized = []
        for result in results:
            entry = asdict(result)
            entry["scenario"]["type"] = getattr(result.scenario.type, "value", None)
            serialized.append(entry)
        return serialized
