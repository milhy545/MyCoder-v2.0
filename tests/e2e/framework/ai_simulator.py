"""
AI behavior simulator for testing.

Simulates AI responses without real API calls.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, List, Optional


class IntelligenceLevel(Enum):
    """Simulated intelligence levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    OPTIMAL = "optimal"


class SimpleAISimulator:
    """
    Minimal AI simulator for quick POC testing.

    Uses pattern matching on prompts to select tools.
    """

    def __init__(self) -> None:
        self.call_count = 0
        self.history: List[Dict[str, Any]] = []

    def simulate(
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Simulate AI response for given prompt.

        Args:
            prompt: User input prompt.
            context: Optional context (files, previous commands, etc.).

        Returns:
            Response dict with tool selection and metadata.
        """
        self.call_count += 1
        prompt_lower = prompt.lower()

        # Multi-step tasks (check FIRST before single commands)
        if self._is_multi_step(prompt_lower):
            return self._handle_multi_step(prompt, context)

        # File operations
        if self._matches_file_read(prompt_lower):
            return self._respond(
                "file_read",
                0.9,
                "Detected file read request",
                alternatives=["bash"],
            )

        if self._matches_file_write(prompt_lower):
            return self._respond(
                "file_write",
                0.9,
                "Detected file write request",
                alternatives=["bash"],
            )

        if self._matches_file_list(prompt_lower):
            return self._respond(
                "file_list",
                0.85,
                "Detected file list request",
                alternatives=["bash"],
            )

        # Git operations
        if self._matches_git_operation(prompt_lower):
            return self._respond(
                "bash",
                0.9,
                "Detected git operation",
                alternatives=["mcp"],
                context_used={"command_type": "git"},
            )

        # Command execution
        if self._matches_bash_command(prompt_lower):
            return self._respond(
                "bash",
                0.85,
                "Detected command execution request",
                alternatives=["mcp"],
            )

        if self._matches_thermal_condition(prompt_lower):
            return self._respond(
                "ask_user",
                0.5,
                "Detected thermal safety concern",
                context_used={
                    "recommended_actions": [
                        "check thermal status",
                        "reduce workload",
                    ]
                },
            )

        if self._matches_provider_issue(prompt_lower):
            return self._respond(
                "ask_user",
                0.5,
                "Detected provider fallback or timeout",
                context_used={
                    "recommended_actions": [
                        "check provider status",
                        "retry fallback",
                    ]
                },
            )

        if self._matches_conflict(prompt_lower) or self._matches_unknown_tool(
            prompt_lower
        ):
            return self._respond(
                "ask_user",
                0.5,
                "Request needs clarification",
                context_used={"recommended_actions": ["ask for clarification"]},
            )

        # Ambiguous - ask for clarification
        return self._respond("ask_user", 0.5, "Request is ambiguous")

    def _matches_file_read(self, prompt: str) -> bool:
        """Check if prompt indicates file read."""
        keywords = ["read", "show", "display", "cat", "view", "open"]
        file_indicators = [
            "file",
            "config",
            ".py",
            ".json",
            ".txt",
            ".md",
            ".yml",
            ".yaml",
            ".toml",
            ".ini",
            ".cfg",
            ".log",
        ]
        return any(kw in prompt for kw in keywords) and any(
            ind in prompt for ind in file_indicators
        )

    def _matches_file_write(self, prompt: str) -> bool:
        """Check if prompt indicates file write."""
        keywords = ["write", "save", "create", "append", "update"]
        file_indicators = ["file", "to", ".py", ".json", ".txt", ".csv", ".md"]
        return any(kw in prompt for kw in keywords) and any(
            ind in prompt for ind in file_indicators
        )

    def _matches_file_list(self, prompt: str) -> bool:
        """Check if prompt indicates file listing."""
        keywords = ["list", "ls", "show files", "directory", "folder", "contents"]
        return any(kw in prompt for kw in keywords)

    def _matches_bash_command(self, prompt: str) -> bool:
        """Check if prompt indicates bash command."""
        keywords = [
            "run",
            "execute",
            "command",
            "shell",
            "terminal",
            "pytest",
            "poetry",
            "install",
            "build",
            "check",
            "update",
        ]
        return any(kw in prompt for kw in keywords)

    def _matches_git_operation(self, prompt: str) -> bool:
        """Check if prompt indicates git operation."""
        git_keywords = [
            "git",
            "commit",
            "push",
            "pull",
            "branch",
            "status",
            "diff",
            "log",
        ]
        return any(kw in prompt for kw in git_keywords)

    def _is_multi_step(self, prompt: str) -> bool:
        """Check if prompt requires multiple steps."""
        multi_indicators = [" and ", " then ", "after that", "next"]
        return any(ind in prompt for ind in multi_indicators)

    def _matches_thermal_condition(self, prompt: str) -> bool:
        """Check if prompt indicates thermal conditions."""
        keywords = ["thermal", "overheat", "temperature", "cpu"]
        return any(kw in prompt for kw in keywords)

    def _matches_provider_issue(self, prompt: str) -> bool:
        """Check if prompt indicates provider issues."""
        keywords = ["provider", "fallback", "timeout"]
        return any(kw in prompt for kw in keywords)

    def _matches_conflict(self, prompt: str) -> bool:
        """Check if prompt contains conflicting instructions."""
        return "delete" in prompt and "keep" in prompt

    def _matches_unknown_tool(self, prompt: str) -> bool:
        """Check if prompt references an unknown tool."""
        return "magic_tool" in prompt

    def _handle_multi_step(
        self, prompt: str, context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle multi-step task."""
        steps = [
            step.strip()
            for step in re.split(r"\s+and\s+|\s+then\s+|,\s*", prompt)
            if step.strip()
        ]
        step_responses = [self.simulate(step, context) for step in steps]

        return {
            "tool": "multi_step",
            "steps": step_responses,
            "confidence": 0.8,
            "reasoning": f"Task requires {len(step_responses)} steps",
        }

    def _respond(
        self,
        tool: str,
        confidence: float,
        reasoning: str,
        alternatives: Optional[List[str]] = None,
        context_used: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate response dict."""
        response = {
            "tool": tool,
            "confidence": confidence,
            "reasoning": reasoning,
            "alternatives": alternatives or [],
            "context_used": context_used or {},
            "call_number": self.call_count,
        }
        self.history.append(response)
        return response


class AISimulator:
    """
    Advanced AI simulator with intelligence levels and context awareness.

    Features:
    - Multiple intelligence levels.
    - Context retention.
    - Tool usage tracking.
    - Response quality simulation.
    """

    def __init__(
        self, intelligence_level: IntelligenceLevel = IntelligenceLevel.NORMAL
    ) -> None:
        self.intelligence = intelligence_level
        self.context_memory: List[Dict[str, Any]] = []
        self.tool_usage_history: List[str] = []
        self.simple_sim = SimpleAISimulator()

    def simulate(
        self, prompt: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Advanced simulation with intelligence levels.

        Args:
            prompt: User input.
            context: Conversation context.

        Returns:
            Enhanced response with context awareness.
        """
        base_response = self.simple_sim.simulate(prompt, context)
        self.tool_usage_history.append(base_response.get("tool", "unknown"))
        if context:
            self.context_memory.append(context)

        if self.intelligence == IntelligenceLevel.LOW:
            return base_response

        if self.intelligence == IntelligenceLevel.NORMAL:
            base_response["context_aware"] = self._check_context(prompt, context)
            return base_response

        if self.intelligence in (IntelligenceLevel.HIGH, IntelligenceLevel.OPTIMAL):
            base_response["context_aware"] = True
            base_response["detailed_reasoning"] = self._generate_reasoning(
                prompt, context, base_response
            )
            base_response["alternatives"] = self._suggest_alternatives(
                base_response.get("tool", "unknown")
            )

            if self.intelligence == IntelligenceLevel.OPTIMAL:
                base_response["optimizations"] = self._suggest_optimizations(
                    prompt, context
                )

            return base_response

        return base_response

    def _check_context(self, prompt: str, context: Optional[Dict[str, Any]]) -> bool:
        """Check if context was used in decision."""
        if not context:
            return False

        prompt_lower = prompt.lower()
        if "current" in prompt_lower and (
            "current_file" in context or "working_directory" in context
        ):
            return True

        return len(context) > 0

    def _generate_reasoning(
        self, prompt: str, context: Optional[Dict[str, Any]], response: Dict[str, Any]
    ) -> str:
        """Generate detailed reasoning for tool selection."""
        tool = response.get("tool", "unknown")
        reasoning = f"Selected '{tool}' because: "

        if tool == "file_read":
            reasoning += "Prompt indicates reading file content. Direct file access is most efficient."
        elif tool == "file_write":
            reasoning += "Prompt indicates writing data to file. File write tool provides safe write operations."
        elif tool == "bash":
            reasoning += (
                "Prompt requires command execution. Bash tool provides shell access."
            )
        elif tool == "multi_step":
            reasoning += (
                f"Task requires {len(response.get('steps', []))} sequential steps."
            )
        else:
            reasoning += "Best match for user intent based on pattern analysis."

        return reasoning

    def _suggest_alternatives(self, selected_tool: str) -> List[str]:
        """Suggest alternative tools that could be used."""
        alternatives_map = {
            "file_read": ["bash"],
            "file_write": ["bash"],
            "file_list": ["bash"],
            "bash": ["mcp"],
        }
        return alternatives_map.get(selected_tool, [])

    def _suggest_optimizations(
        self, prompt: str, context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Suggest optimizations for optimal intelligence."""
        optimizations: List[str] = []
        prompt_lower = prompt.lower()

        if "file" in prompt_lower and context and "working_directory" in context:
            optimizations.append("Use relative path from working directory")

        if "git" in prompt_lower:
            optimizations.append("Could batch git commands for efficiency")

        if "and" in prompt_lower:
            optimizations.append("Consider parallel execution for independent steps")

        return optimizations
