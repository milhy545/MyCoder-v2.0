"""Proposal generation for self-evolve patches."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from .models import EvolveSignal


@dataclass
class ProposalDraft:
    """Intermediate proposal payload."""

    summary: str
    rationale: str
    diff: str
    error: Optional[str] = None


class ProposalEngine:
    """Generate patch proposals using the configured coder."""

    def __init__(self, coder, repo_root: Path, allowed_paths: Optional[list[str]] = None):
        self.coder = coder
        self.repo_root = repo_root
        self.allowed_paths = allowed_paths or []

    async def generate(self, signal: EvolveSignal) -> ProposalDraft:
        prompt = self._build_prompt(signal)
        response = await self.coder.process_request(
            prompt,
            use_tools=False,
        )
        content = response.get("content") if isinstance(response, dict) else str(response)
        payload = self._extract_json(content)
        if payload:
            diff = payload.get("diff", "")
            return ProposalDraft(
                summary=payload.get("summary", ""),
                rationale=payload.get("rationale", ""),
                diff=diff,
                error=None,
            )

        diff = self._extract_diff(content)
        if not diff:
            return ProposalDraft(
                summary="",
                rationale="",
                diff="",
                error="Failed to extract diff from model output",
            )
        return ProposalDraft(
            summary="Generated patch",
            rationale="",
            diff=diff,
            error=None,
        )

    def _build_prompt(self, signal: EvolveSignal) -> str:
        status = self._git_status()
        allowed_text = ", ".join(self.allowed_paths) if self.allowed_paths else "repo root"
        return (
            "You are the Self-Evolve engine for MyCoder. "
            "Use the failing test output to propose a minimal fix. "
            "Return ONLY JSON with keys: summary, rationale, diff. "
            "The diff must be unified diff format. "
            f"Only touch files under: {allowed_text}.\n\n"
            f"Test summary: {signal.summary}\n\n"
            f"Failing output:\n{signal.failure_output}\n\n"
            f"Git status:\n{status}\n"
        )

    def _git_status(self) -> str:
        try:
            import subprocess

            result = subprocess.run(
                ["git", "status", "-sb"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            return result.stdout.strip() or result.stderr.strip()
        except Exception:
            return "Git status unavailable"

    def _extract_json(self, content: str) -> Optional[Dict[str, Any]]:
        content = content.strip()
        if not content:
            return None

        json_block = None
        if content.startswith("```"):
            match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", content)
            if match:
                json_block = match.group(1)
        elif content.startswith("{"):
            json_block = content

        if not json_block:
            return None

        try:
            return json.loads(json_block)
        except json.JSONDecodeError:
            return None

    def _extract_diff(self, content: str) -> str:
        match = re.search(r"```diff\s*([\s\S]*?)```", content)
        if match:
            return match.group(1).strip()
        if content.lstrip().startswith("diff --git"):
            return content.strip()
        return ""
