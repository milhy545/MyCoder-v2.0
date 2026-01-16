"""
AI-specific assertion framework for E2E tests.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


class AIAssertionError(AssertionError):
    """Assertion error for AI behavior validation."""


class AIAssertions:
    """AI behavior assertions with clear failure messages."""

    def assert_tool_selected(self, response: Dict[str, Any], expected_tool: str) -> None:
        """Assert that the expected tool was selected."""
        actual_tool = response.get("tool")
        if actual_tool != expected_tool:
            raise AIAssertionError(
                f"Tool mismatch: expected '{expected_tool}', got '{actual_tool}'"
            )

    def assert_tool_confidence(
        self, response: Dict[str, Any], min_confidence: float = 0.8
    ) -> None:
        """Assert minimum confidence score."""
        confidence = response.get("confidence", 0.0)
        if confidence < min_confidence:
            raise AIAssertionError(
                f"Confidence too low: expected >= {min_confidence}, got {confidence}"
            )

    def assert_context_used(
        self, response: Dict[str, Any], required_keys: Iterable[str]
    ) -> None:
        """Assert that specific context keys were used."""
        context_used = response.get("context_used", {})
        missing = [key for key in required_keys if key not in context_used]
        if missing:
            raise AIAssertionError(f"Missing context keys: {missing}")

    def assert_context_retained(
        self, response: Dict[str, Any], previous_context: Dict[str, Any]
    ) -> None:
        """Assert that context was retained between turns."""
        if not previous_context:
            raise AIAssertionError("Previous context is empty")

        context_used = response.get("context_used", {})
        if not context_used:
            raise AIAssertionError("Response did not use any context")

        missing = [
            key for key, value in previous_context.items() if context_used.get(key) != value
        ]
        if missing:
            raise AIAssertionError(f"Context not retained for keys: {missing}")

    def assert_multi_step(
        self, response: Dict[str, Any], expected_steps: Optional[int] = None
    ) -> None:
        """Assert that response represents a multi-step plan."""
        if response.get("tool") != "multi_step":
            raise AIAssertionError("Response is not a multi-step plan")

        steps = response.get("steps", [])
        if not steps:
            raise AIAssertionError("Multi-step response has no steps")

        if expected_steps is not None and len(steps) != expected_steps:
            raise AIAssertionError(
                f"Expected {expected_steps} steps, got {len(steps)}"
            )

    def assert_step_tool(
        self, response: Dict[str, Any], step_index: int, expected_tool: str
    ) -> None:
        """Assert the tool selected for a given step."""
        steps = response.get("steps", [])
        if step_index < 0 or step_index >= len(steps):
            raise AIAssertionError("Step index out of range")

        actual_tool = steps[step_index].get("tool")
        if actual_tool != expected_tool:
            raise AIAssertionError(
                f"Step {step_index} tool mismatch: expected '{expected_tool}', got '{actual_tool}'"
            )

    def assert_response_quality(
        self, response: Dict[str, Any], min_score: float = 0.8
    ) -> None:
        """Assert response quality score."""
        quality = response.get("quality_score")
        if quality is None:
            raise AIAssertionError("Response missing quality_score")
        if quality < min_score:
            raise AIAssertionError(
                f"Quality score too low: expected >= {min_score}, got {quality}"
            )

    def assert_reasoning_present(self, response: Dict[str, Any]) -> None:
        """Assert that reasoning field is present and non-empty."""
        reasoning = response.get("reasoning") or response.get("detailed_reasoning")
        if not reasoning:
            raise AIAssertionError("Response missing reasoning")

    def assert_prompt_followed(self, response: Dict[str, Any], expected_keywords: List[str]) -> None:
        """Assert that response reasoning mentions expected prompt keywords."""
        reasoning = response.get("reasoning", "") + " " + response.get(
            "detailed_reasoning", ""
        )
        missing = [kw for kw in expected_keywords if kw.lower() not in reasoning.lower()]
        if missing:
            raise AIAssertionError(f"Reasoning missing expected keywords: {missing}")

    def assert_error_handled(self, response: Dict[str, Any]) -> None:
        """Assert that error was handled gracefully."""
        if response.get("error") and not response.get("recovery_suggestions"):
            raise AIAssertionError("Error present but no recovery suggestions provided")
