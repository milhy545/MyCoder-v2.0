"""Risk assessment for self-evolve proposals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class RiskAssessment:
    """Risk assessment output."""

    score: float
    notes: List[str]


class RiskAssessor:
    """Heuristic risk scoring for proposed diffs."""

    def assess(self, diff: str) -> RiskAssessment:
        score = 0.1
        notes: List[str] = []
        paths = self._extract_paths(diff)
        lines_changed = self._count_changed_lines(diff)

        if any(path.startswith("src/") for path in paths):
            score += 0.25
            notes.append("Touches source code")
        if any(path.startswith("tests/") for path in paths):
            score += 0.05
            notes.append("Touches tests")
        if any(path.startswith("docs/") for path in paths):
            score += 0.02
            notes.append("Touches documentation")
        if any(path in {"pyproject.toml", "docker-compose.yml"} for path in paths):
            score += 0.2
            notes.append("Touches critical configuration")
        if any(path.endswith(".json") for path in paths):
            score += 0.05
            notes.append("Touches JSON config")

        if lines_changed > 500:
            score += 0.2
            notes.append("Large diff (>500 lines)")
        if lines_changed > 1000:
            score += 0.1
            notes.append("Very large diff (>1000 lines)")

        score = max(0.0, min(1.0, score))
        return RiskAssessment(score=score, notes=notes)

    def _extract_paths(self, diff: str) -> List[str]:
        paths = []
        for line in diff.splitlines():
            if line.startswith("diff --git "):
                parts = line.split()
                if len(parts) >= 4:
                    path = parts[2].replace("a/", "", 1)
                    paths.append(path)
        return paths

    def _count_changed_lines(self, diff: str) -> int:
        count = 0
        for line in diff.splitlines():
            if line.startswith("+++") or line.startswith("---"):
                continue
            if line.startswith("+") or line.startswith("-"):
                count += 1
        return count
