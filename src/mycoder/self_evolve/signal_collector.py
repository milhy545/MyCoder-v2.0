"""Collect self-evolve signals from test runs."""

from __future__ import annotations

from typing import List

from .models import EvolveSignal, TestCommandResult, TestRunSummary


class SignalCollector:
    """Build evolve signals from test results."""

    def __init__(self, max_output_chars: int = 8000) -> None:
        self.max_output_chars = max_output_chars

    def build_signal(self, test_run: TestRunSummary) -> EvolveSignal:
        failures = test_run.failures()
        summary = self._summarize_failures(failures)
        failure_output = self._collect_failure_output(failures)
        return EvolveSignal(
            summary=summary,
            failure_output=failure_output,
            test_run=test_run,
        )

    def _summarize_failures(self, failures: List[TestCommandResult]) -> str:
        if not failures:
            return "All tests passed."
        summaries = [
            f"{failure.command} (exit {failure.exit_code})" for failure in failures
        ]
        return "Failed commands: " + ", ".join(summaries)

    def _collect_failure_output(self, failures: List[TestCommandResult]) -> str:
        if not failures:
            return ""
        blocks = []
        for failure in failures:
            output = failure.stdout + "\n" + failure.stderr
            output = output.strip()
            if len(output) > self.max_output_chars:
                output = output[-self.max_output_chars :]
            blocks.append(f"$ {failure.command}\n{output}\n")
        return "\n".join(blocks).strip()
