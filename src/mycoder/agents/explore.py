"""Fast agent for exploring codebases."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .base import BaseAgent, AgentResult, AgentType


class ExploreAgent(BaseAgent):
    """Agent for quick codebase exploration."""

    @property
    def agent_type(self) -> AgentType:
        return AgentType.EXPLORE

    @property
    def description(self) -> str:
        return "Fast codebase exploration: find files, search code, understand structure"

    async def execute(self, task: str, context: Dict[str, Any] = None) -> AgentResult:
        thoroughness = context.get("thoroughness", "medium") if context else "medium"

        if self._is_file_search(task):
            result = await self._search_files(task, thoroughness)
        elif self._is_code_search(task):
            result = await self._search_code(task, thoroughness)
        else:
            result = await self._explore_structure(task, thoroughness)

        return AgentResult(
            success=True,
            content=result,
            agent_type=self.agent_type,
            metadata={"thoroughness": thoroughness},
        )

    def _is_file_search(self, task: str) -> bool:
        keywords = ["find file", "where is", "locate", "*.py", "*.js", "*.ts"]
        return any(keyword in task.lower() for keyword in keywords)

    def _is_code_search(self, task: str) -> bool:
        keywords = ["search for", "find code", "grep", "where is function", "class"]
        return any(keyword in task.lower() for keyword in keywords)

    async def _search_files(self, task: str, thoroughness: str) -> str:
        patterns = self._extract_patterns(task)
        results: List[Path] = []

        for pattern in patterns:
            matches = list(self.working_dir.rglob(pattern))
            results.extend(matches[:50])

        if not results:
            return "No files found matching the pattern."

        return "\n".join(str(path.relative_to(self.working_dir)) for path in results)

    async def _search_code(self, task: str, thoroughness: str) -> str:
        import subprocess

        search_term = self._extract_search_term(task)
        if not search_term:
            return "Could not determine search term."

        try:
            result = subprocess.run(
                [
                    "rg",
                    "-n",
                    "--glob",
                    "*.py",
                    "--glob",
                    "*.md",
                    search_term,
                    str(self.working_dir),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout.strip()
            return output[:5000] if output else "No matches found."
        except Exception as exc:
            return f"Search error: {exc}"

    async def _explore_structure(self, task: str, thoroughness: str) -> str:
        structure = []
        for item in sorted(self.working_dir.iterdir()):
            if item.name.startswith("."):
                continue
            prefix = "DIR" if item.is_dir() else "FILE"
            structure.append(f"{prefix} {item.name}")

        return "\n".join(structure)

    def _extract_patterns(self, task: str) -> List[str]:
        import re

        patterns = re.findall(r"\*\.\w+|\*\*/\*\.\w+", task)
        return patterns if patterns else ["*.py"]

    def _extract_search_term(self, task: str) -> str:
        import re

        quoted = re.search(r'["\']([^"\']+)["\']', task)
        if quoted:
            return quoted.group(1)

        for_match = re.search(r"(?:search|find|grep)\s+(?:for\s+)?(\w+)", task.lower())
        if for_match:
            return for_match.group(1)

        return ""
