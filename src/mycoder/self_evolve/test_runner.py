"""Test runner for self-evolve flows."""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from datetime import datetime, timezone
from typing import List

from .models import TestCommandResult, TestRunSummary


class TestRunner:
    """Run test commands and capture output."""

    def __init__(self, working_directory, timeout_seconds: int = 900) -> None:
        self.working_directory = working_directory
        self.timeout_seconds = timeout_seconds

    def run_commands(self, commands: List[str]) -> TestRunSummary:
        started_at = datetime.now(timezone.utc).isoformat()
        start_time = time.time()
        results = []

        for command in commands:
            cmd_start = time.time()
            try:
                args = shlex.split(command, posix=os.name != "nt")
            except ValueError as exc:
                duration_ms = int((time.time() - cmd_start) * 1000)
                results.append(
                    TestCommandResult(
                        command=command,
                        exit_code=1,
                        stdout="",
                        stderr=str(exc),
                        duration_ms=duration_ms,
                    )
                )
                continue

            if not args:
                duration_ms = int((time.time() - cmd_start) * 1000)
                results.append(
                    TestCommandResult(
                        command=command,
                        exit_code=1,
                        stdout="",
                        stderr="Command is empty",
                        duration_ms=duration_ms,
                    )
                )
                continue

            process = subprocess.run(
                args,
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
            duration_ms = int((time.time() - cmd_start) * 1000)
            results.append(
                TestCommandResult(
                    command=command,
                    exit_code=process.returncode,
                    stdout=process.stdout or "",
                    stderr=process.stderr or "",
                    duration_ms=duration_ms,
                )
            )

        total_duration = int((time.time() - start_time) * 1000)
        return TestRunSummary(
            started_at=started_at,
            duration_ms=total_duration,
            results=results,
        )
