"""
Scenario engine for E2E testing.

Defines and executes test scenarios.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class ScenarioType(Enum):
    """Types of test scenarios."""

    PROMPT_ENGINEERING = "prompt_engineering"
    TOOL_SELECTION = "tool_selection"
    CONTEXT_AWARENESS = "context_awareness"
    ERROR_HANDLING = "error_handling"
    MULTI_STEP = "multi_step"


@dataclass
class ScenarioDefinition:
    """
    Definition of a test scenario.

    Attributes:
        name: Scenario name.
        type: Scenario type.
        user_input: Input from user.
        expected_tool: Expected tool to be selected.
        expected_confidence: Minimum expected confidence.
        context: Optional context for the scenario.
        validation_rules: Custom validation functions.
        description: Human-readable description.
    """

    name: str
    type: ScenarioType
    user_input: str
    expected_tool: str
    expected_confidence: float = 0.7
    context: Optional[Dict[str, Any]] = None
    validation_rules: List[Callable[[Dict[str, Any]], bool]] = field(
        default_factory=list
    )
    description: str = ""

    def __post_init__(self) -> None:
        """Validate scenario definition."""
        if not self.name:
            raise ValueError("Scenario must have a name")
        if not self.user_input:
            raise ValueError("Scenario must have user_input")
        if not self.expected_tool:
            raise ValueError("Scenario must have expected_tool")


@dataclass
class ScenarioResult:
    """
    Result of scenario execution.

    Attributes:
        scenario: The executed scenario.
        passed: Whether scenario passed.
        actual_tool: Tool that was actually selected.
        actual_confidence: Confidence of the selection.
        failures: List of validation failures.
        execution_time_ms: Time taken to execute.
        metadata: Additional metadata.
    """

    scenario: ScenarioDefinition
    passed: bool
    actual_tool: str
    actual_confidence: float
    failures: List[str] = field(default_factory=list)
    execution_time_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ScenarioEngine:
    """
    Executes test scenarios and validates results.

    Features:
    - Run individual scenarios.
    - Run scenario suites.
    - Validate results against expectations.
    - Collect metrics.
    """

    def __init__(self, ai_simulator: Any) -> None:
        """
        Initialize scenario engine.

        Args:
            ai_simulator: AI simulator instance to use for testing.
        """
        self.simulator = ai_simulator
        self.results: List[ScenarioResult] = []

    def execute_scenario(self, scenario: ScenarioDefinition) -> ScenarioResult:
        """
        Execute a single test scenario.

        Args:
            scenario: Scenario to execute.

        Returns:
            ScenarioResult with execution details.
        """
        import time

        start_time = time.time()

        response = self.simulator.simulate(
            scenario.user_input,
            context=scenario.context,
        )

        execution_time_ms = int((time.time() - start_time) * 1000)

        failures = self._validate_response(scenario, response)
        passed = len(failures) == 0

        result = ScenarioResult(
            scenario=scenario,
            passed=passed,
            actual_tool=response.get("tool", "unknown"),
            actual_confidence=response.get("confidence", 0.0),
            failures=failures,
            execution_time_ms=execution_time_ms,
            metadata={"response": response},
        )

        self.results.append(result)
        return result

    def _validate_response(
        self, scenario: ScenarioDefinition, response: Dict[str, Any]
    ) -> List[str]:
        """
        Validate AI response against scenario expectations.

        Args:
            scenario: Expected scenario.
            response: Actual response from simulator.

        Returns:
            List of validation failure messages (empty if all passed).
        """
        failures: List[str] = []

        actual_tool = response.get("tool")
        if actual_tool != scenario.expected_tool:
            failures.append(
                f"Tool mismatch: expected '{scenario.expected_tool}', got '{actual_tool}'"
            )

        actual_confidence = response.get("confidence", 0.0)
        if actual_confidence < scenario.expected_confidence:
            failures.append(
                "Confidence too low: expected >= "
                f"{scenario.expected_confidence}, got {actual_confidence}"
            )

        for rule in scenario.validation_rules:
            try:
                rule_result = rule(response)
                if not rule_result:
                    failures.append(f"Custom validation failed: {rule.__name__}")
            except Exception as exc:
                failures.append(f"Custom validation error: {exc}")

        return failures

    def execute_suite(
        self, scenarios: List[ScenarioDefinition]
    ) -> List[ScenarioResult]:
        """
        Execute multiple scenarios.

        Args:
            scenarios: List of scenarios to execute.

        Returns:
            List of scenario results.
        """
        results: List[ScenarioResult] = []
        for scenario in scenarios:
            results.append(self.execute_scenario(scenario))

        return results

    def get_pass_rate(self) -> float:
        """Calculate pass rate for executed scenarios."""
        if not self.results:
            return 0.0

        passed = sum(1 for result in self.results if result.passed)
        return passed / len(self.results)

    def get_failures(self) -> List[ScenarioResult]:
        """Get all failed scenarios."""
        return [result for result in self.results if not result.passed]

    def reset(self) -> None:
        """Reset results."""
        self.results = []


COMMON_SCENARIOS = [
    ScenarioDefinition(
        name="simple_file_read",
        type=ScenarioType.TOOL_SELECTION,
        user_input="Read mycoder_config.json",
        expected_tool="file_read",
        expected_confidence=0.8,
        description="Basic file read operation",
    ),
    ScenarioDefinition(
        name="bash_command",
        type=ScenarioType.TOOL_SELECTION,
        user_input="Run pytest tests/",
        expected_tool="bash",
        expected_confidence=0.8,
        description="Basic command execution",
    ),
    ScenarioDefinition(
        name="multi_step_workflow",
        type=ScenarioType.MULTI_STEP,
        user_input="Update dependencies and run tests",
        expected_tool="multi_step",
        expected_confidence=0.7,
        description="Multi-step task requiring planning",
    ),
]
