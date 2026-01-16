# TASK: AI Testing Framework - E2E Self-Testing Suite

## CONTEXT

Claude Code navrhl kompletní **AI Testing Framework** pro autonomní testování AI logiky, promptů a tool selection v MyCoder v2.1.1. Framework umožní AI agentům (včetně Claude Code) samostatně testovat a iterovat změny bez lidského zásahu.

**Dokumentace k prostudování:**
- `tests/e2e/AI_TESTING_FRAMEWORK.md` - Kompletní architektura frameworku
- `tests/e2e/IMPLEMENTATION_PLAN.md` - Prioritizovaný implementační plán
- `tests/e2e/test_simulation.py` - Existující E2E test jako referenční implementace
- `tests/functional/test_mycoder_live.py` - Funkční testy jako vzor

**Stav projektu:**
- ✅ MyCoder v2.1.1 nasazen (commit a57a99b)
- ✅ 299 testů passed (259 unit + 40 integration)
- ✅ Framework design kompletní
- ⏳ Implementace pending

## ÚKOL

Implementuj **AI Testing Framework** podle následující struktury a priorit.

---

## FÁZE 1: Foundation & POC (Proof of Concept)

### CÍL
Vytvořit minimal working prototype frameworku s demonstračními testy.

---

### TODO 1.1: Vytvořit strukturu directories

```bash
mkdir -p tests/e2e/framework
mkdir -p tests/e2e/scenarios
mkdir -p tests/e2e/fixtures
mkdir -p tests/e2e/reports
touch tests/e2e/framework/__init__.py
touch tests/e2e/scenarios/__init__.py
```

---

### TODO 1.2: Implementovat AI Simulator (MVP)

**File:** `tests/e2e/framework/ai_simulator.py` (~400 řádků)

**Požadavky:**

1. **Class `SimpleAISimulator`** - Minimal viable simulator
   - Pattern-based response selection
   - Support pro common scenarios (file ops, bash commands, git)
   - Deterministic behavior (reproducible tests)

2. **Class `AISimulator`** (advanced) - Full simulator
   - Multiple intelligence levels ("low", "normal", "high", "optimal")
   - Tool usage tracking
   - Context awareness simulation
   - Configurable response patterns

3. **Response Format:**
```python
{
    "tool": "file_read",              # Selected tool
    "confidence": 0.9,                # Confidence score 0-1
    "reasoning": "File read is...",   # Why this tool was selected
    "alternatives": ["bash"],         # Alternative tools considered
    "context_used": ["file_path"],    # What context was used
    "steps": [...]                    # For multi-step tasks
}
```

**Template:**

```python
"""
AI Behavior Simulator for Testing
Simulates AI responses without real API calls.
"""

import re
from typing import Dict, List, Optional, Any
from enum import Enum


class IntelligenceLevel(Enum):
    """Simulated intelligence levels"""
    LOW = "low"           # Basic pattern matching
    NORMAL = "normal"     # Good pattern matching + some context
    HIGH = "high"         # Advanced reasoning + full context
    OPTIMAL = "optimal"   # Perfect tool selection + planning


class SimpleAISimulator:
    """
    Minimal AI simulator for quick POC testing.

    Uses pattern matching on prompts to select tools.
    """

    def __init__(self):
        self.call_count = 0
        self.history = []

    def simulate(self, prompt: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Simulate AI response for given prompt.

        Args:
            prompt: User input prompt
            context: Optional context (files, previous commands, etc.)

        Returns:
            Response dict with tool selection and metadata
        """
        self.call_count += 1
        prompt_lower = prompt.lower()

        # File operations
        if self._matches_file_read(prompt_lower):
            return self._respond("file_read", 0.9, "Detected file read request")

        if self._matches_file_write(prompt_lower):
            return self._respond("file_write", 0.9, "Detected file write request")

        if self._matches_file_list(prompt_lower):
            return self._respond("file_list", 0.85, "Detected file list request")

        # Command execution
        if self._matches_bash_command(prompt_lower):
            return self._respond("bash", 0.85, "Detected command execution request")

        # Git operations
        if self._matches_git_operation(prompt_lower):
            return self._respond("bash", 0.9, "Detected git operation",
                                context={"command_type": "git"})

        # Multi-step tasks
        if self._is_multi_step(prompt_lower):
            return self._handle_multi_step(prompt, context)

        # Ambiguous - ask for clarification
        return self._respond("ask_user", 0.5, "Request is ambiguous")

    def _matches_file_read(self, prompt: str) -> bool:
        """Check if prompt indicates file read"""
        keywords = ["read", "show", "display", "cat", "view", "open"]
        file_indicators = ["file", "config", ".py", ".json", ".txt", ".md"]
        return any(kw in prompt for kw in keywords) and any(ind in prompt for ind in file_indicators)

    def _matches_file_write(self, prompt: str) -> bool:
        """Check if prompt indicates file write"""
        keywords = ["write", "save", "create", "append", "update"]
        file_indicators = ["file", "to", ".py", ".json", ".txt"]
        return any(kw in prompt for kw in keywords) and any(ind in prompt for ind in file_indicators)

    def _matches_file_list(self, prompt: str) -> bool:
        """Check if prompt indicates file listing"""
        keywords = ["list", "ls", "show files", "directory", "folder"]
        return any(kw in prompt for kw in keywords)

    def _matches_bash_command(self, prompt: str) -> bool:
        """Check if prompt indicates bash command"""
        keywords = ["run", "execute", "command", "shell", "terminal"]
        return any(kw in prompt for kw in keywords)

    def _matches_git_operation(self, prompt: str) -> bool:
        """Check if prompt indicates git operation"""
        git_keywords = ["git", "commit", "push", "pull", "branch", "status", "diff", "log"]
        return any(kw in prompt for kw in git_keywords)

    def _is_multi_step(self, prompt: str) -> bool:
        """Check if prompt requires multiple steps"""
        multi_indicators = [" and ", " then ", ",", "after that", "next"]
        return any(ind in prompt for ind in multi_indicators)

    def _handle_multi_step(self, prompt: str, context: Optional[Dict]) -> Dict[str, Any]:
        """Handle multi-step task"""
        # Split on common separators
        steps = re.split(r'\s+and\s+|\s+then\s+|,\s*', prompt)
        step_responses = [self.simulate(step.strip(), context) for step in steps if step.strip()]

        return {
            "tool": "multi_step",
            "steps": step_responses,
            "confidence": 0.8,
            "reasoning": f"Task requires {len(step_responses)} steps",
        }

    def _respond(self, tool: str, confidence: float, reasoning: str,
                 alternatives: Optional[List[str]] = None,
                 context: Optional[Dict] = None) -> Dict[str, Any]:
        """Generate response dict"""
        response = {
            "tool": tool,
            "confidence": confidence,
            "reasoning": reasoning,
            "alternatives": alternatives or [],
            "context_used": context or {},
            "call_number": self.call_count,
        }
        self.history.append(response)
        return response


class AISimulator:
    """
    Advanced AI simulator with intelligence levels and context awareness.

    Features:
    - Multiple intelligence levels
    - Context retention
    - Tool usage tracking
    - Response quality simulation
    """

    def __init__(self, intelligence_level: IntelligenceLevel = IntelligenceLevel.NORMAL):
        self.intelligence = intelligence_level
        self.context_memory = []
        self.tool_usage_history = []
        self.simple_sim = SimpleAISimulator()

    def simulate(self, prompt: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Advanced simulation with intelligence levels.

        Args:
            prompt: User input
            context: Conversation context

        Returns:
            Enhanced response with context awareness
        """
        # Use simple simulator as base
        base_response = self.simple_sim.simulate(prompt, context)

        # Enhance based on intelligence level
        if self.intelligence == IntelligenceLevel.LOW:
            # Low intelligence: just return base response
            return base_response

        if self.intelligence == IntelligenceLevel.NORMAL:
            # Normal: add some context awareness
            base_response["context_aware"] = self._check_context(prompt, context)
            return base_response

        if self.intelligence in [IntelligenceLevel.HIGH, IntelligenceLevel.OPTIMAL]:
            # High/Optimal: full context + reasoning + alternatives
            base_response["context_aware"] = True
            base_response["detailed_reasoning"] = self._generate_reasoning(prompt, context, base_response)
            base_response["alternatives"] = self._suggest_alternatives(base_response["tool"])

            if self.intelligence == IntelligenceLevel.OPTIMAL:
                # Optimal: also suggest optimizations
                base_response["optimizations"] = self._suggest_optimizations(prompt, context)

            return base_response

        return base_response

    def _check_context(self, prompt: str, context: Optional[Dict]) -> bool:
        """Check if context was used in decision"""
        if not context:
            return False
        # Simple heuristic: was context relevant?
        return len(context) > 0

    def _generate_reasoning(self, prompt: str, context: Optional[Dict], response: Dict) -> str:
        """Generate detailed reasoning for tool selection"""
        tool = response["tool"]
        reasoning = f"Selected '{tool}' because: "

        if tool == "file_read":
            reasoning += "Prompt indicates reading file content. Direct file access is most efficient."
        elif tool == "file_write":
            reasoning += "Prompt indicates writing data to file. File write tool provides safe write operations."
        elif tool == "bash":
            reasoning += "Prompt requires command execution. Bash tool provides shell access."
        elif tool == "multi_step":
            reasoning += f"Task requires {len(response.get('steps', []))} sequential steps."
        else:
            reasoning += "Best match for user intent based on pattern analysis."

        return reasoning

    def _suggest_alternatives(self, selected_tool: str) -> List[str]:
        """Suggest alternative tools that could be used"""
        alternatives_map = {
            "file_read": ["bash"],  # Could use cat
            "file_write": ["bash"],  # Could use echo/printf
            "file_list": ["bash"],   # Could use ls
            "bash": ["mcp"],         # Could use MCP if available
        }
        return alternatives_map.get(selected_tool, [])

    def _suggest_optimizations(self, prompt: str, context: Optional[Dict]) -> List[str]:
        """Suggest optimizations for optimal intelligence"""
        optimizations = []

        if "file" in prompt.lower() and context and "working_directory" in context:
            optimizations.append("Use relative path from working directory")

        if "git" in prompt.lower():
            optimizations.append("Could batch git commands for efficiency")

        if "and" in prompt.lower():
            optimizations.append("Consider parallel execution for independent steps")

        return optimizations


# TODO: Add more sophisticated patterns
# TODO: Implement learning from test failures
# TODO: Add response caching for reproducibility
```

**Testovací strategie:**
- Pattern matching works correctly
- Multi-step task detection
- Intelligence levels produce different outputs
- Deterministic for same inputs

---

### TODO 1.3: Vytvořit POC Test Suite

**File:** `tests/e2e/test_poc_tool_selection.py` (~300 řádků)

**Požadavky:**

Test základní funkcionalitu AI simulatoru:
- File operations (read, write, list)
- Command execution (bash, git)
- Multi-step tasks
- Ambiguous requests
- Context awareness

**Template:**

```python
"""
Proof of Concept - Tool Selection Testing

Validates that AI simulator correctly selects tools for common scenarios.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from tests.e2e.framework.ai_simulator import SimpleAISimulator, AISimulator, IntelligenceLevel


class TestSimpleAISimulatorPOC:
    """POC tests for SimpleAISimulator"""

    def setup_method(self):
        """Setup before each test"""
        self.simulator = SimpleAISimulator()

    def test_file_read_operations(self):
        """Test file reading scenarios"""
        test_cases = [
            ("Read mycoder_config.json", "file_read"),
            ("Show me the contents of api_providers.py", "file_read"),
            ("Display the README file", "file_read"),
            ("Cat the setup.py", "file_read"),
        ]

        for prompt, expected_tool in test_cases:
            result = self.simulator.simulate(prompt)
            assert result["tool"] == expected_tool, \
                f"Failed for '{prompt}': expected {expected_tool}, got {result['tool']}"
            assert result["confidence"] > 0.8, "Confidence too low"

    def test_file_write_operations(self):
        """Test file writing scenarios"""
        test_cases = [
            ("Write 'Hello' to output.txt", "file_write"),
            ("Create a new file config.json", "file_write"),
            ("Save data to results.csv", "file_write"),
        ]

        for prompt, expected_tool in test_cases:
            result = self.simulator.simulate(prompt)
            assert result["tool"] == expected_tool
            assert result["confidence"] > 0.8

    def test_file_list_operations(self):
        """Test file listing scenarios"""
        test_cases = [
            ("List files in src/", "file_list"),
            ("Show directory contents", "file_list"),
            ("ls the current folder", "file_list"),
        ]

        for prompt, expected_tool in test_cases:
            result = self.simulator.simulate(prompt)
            assert result["tool"] == expected_tool

    def test_bash_command_execution(self):
        """Test bash command scenarios"""
        test_cases = [
            ("Run pytest", "bash"),
            ("Execute poetry install", "bash"),
            ("Run the build script", "bash"),
        ]

        for prompt, expected_tool in test_cases:
            result = self.simulator.simulate(prompt)
            assert result["tool"] == expected_tool

    def test_git_operations(self):
        """Test git command scenarios"""
        test_cases = [
            ("Check git status", "bash"),
            ("Show git log", "bash"),
            ("Create a new branch", "bash"),
            ("Commit the changes", "bash"),
        ]

        for prompt, expected_tool in test_cases:
            result = self.simulator.simulate(prompt)
            assert result["tool"] == expected_tool
            # Git operations should have context
            if "context_used" in result:
                assert result["context_used"].get("command_type") == "git"

    def test_multi_step_tasks(self):
        """Test multi-step task planning"""
        result = self.simulator.simulate(
            "Update dependencies and run tests",
            context={"working_dir": "/project"}
        )

        # Should break into multiple steps
        assert result["tool"] == "multi_step"
        assert "steps" in result
        assert len(result["steps"]) >= 2

        # Verify steps are reasonable
        steps = result["steps"]
        # Should have bash commands
        assert any(step["tool"] == "bash" for step in steps)

    def test_ambiguous_requests(self):
        """Test handling of ambiguous requests"""
        ambiguous_prompts = [
            "Fix the bug",
            "Make it better",
            "Optimize",
        ]

        for prompt in ambiguous_prompts:
            result = self.simulator.simulate(prompt)

            # Should ask for clarification or have low confidence
            assert (
                result["tool"] == "ask_user"
                or result["confidence"] < 0.7
            ), f"Ambiguous prompt '{prompt}' should have low confidence or ask user"

    def test_simulator_history_tracking(self):
        """Test that simulator tracks call history"""
        self.simulator.simulate("Read file.txt")
        self.simulator.simulate("Write to output.txt")

        assert self.simulator.call_count == 2
        assert len(self.simulator.history) == 2
        assert self.simulator.history[0]["tool"] == "file_read"
        assert self.simulator.history[1]["tool"] == "file_write"


class TestAdvancedAISimulatorPOC:
    """POC tests for AISimulator with intelligence levels"""

    def test_intelligence_levels(self):
        """Test different intelligence levels produce different outputs"""
        prompt = "Read config.json and update version"

        # Low intelligence
        sim_low = AISimulator(intelligence_level=IntelligenceLevel.LOW)
        result_low = sim_low.simulate(prompt)

        # High intelligence
        sim_high = AISimulator(intelligence_level=IntelligenceLevel.HIGH)
        result_high = sim_high.simulate(prompt)

        # Both should detect multi-step, but high should have more detail
        assert result_low["tool"] == result_high["tool"]

        # High intelligence should have additional fields
        if result_high["tool"] == "multi_step":
            assert "detailed_reasoning" in result_high
            assert "alternatives" in result_high

    def test_optimal_intelligence_optimizations(self):
        """Test optimal intelligence suggests optimizations"""
        sim_optimal = AISimulator(intelligence_level=IntelligenceLevel.OPTIMAL)

        result = sim_optimal.simulate(
            "Run tests and check coverage",
            context={"working_directory": "/project"}
        )

        # Optimal should suggest optimizations
        if "optimizations" in result:
            assert len(result["optimizations"]) > 0

    def test_context_awareness(self):
        """Test that simulator uses context"""
        sim = AISimulator(intelligence_level=IntelligenceLevel.HIGH)

        context = {
            "working_directory": "/project",
            "current_file": "api_providers.py"
        }

        result = sim.simulate("Show the current file", context=context)

        # Should be context-aware
        assert result.get("context_aware") is True


class TestScenarioIntegration:
    """Integration tests combining multiple scenarios"""

    def test_realistic_workflow(self):
        """Test realistic development workflow"""
        simulator = SimpleAISimulator()

        # Scenario: Developer wants to update code and test
        steps = [
            ("Read api_providers.py", "file_read"),
            ("Update the file with new code", "file_write"),
            ("Run the tests", "bash"),
            ("Check git status", "bash"),
        ]

        for prompt, expected_tool in steps:
            result = simulator.simulate(prompt)
            assert result["tool"] == expected_tool, \
                f"Workflow step failed: '{prompt}'"

    def test_error_recovery_scenario(self):
        """Test handling of error scenarios"""
        simulator = SimpleAISimulator()

        # Try to read non-existent file
        result = simulator.simulate("Read nonexistent_file.txt")

        # Should still select file_read (simulator doesn't know file doesn't exist)
        assert result["tool"] == "file_read"

        # In real usage, tool would fail and AI would need to recover
        # That's tested in full E2E scenarios


# TODO: Add more complex scenarios
# TODO: Test edge cases
# TODO: Add performance benchmarks
```

---

### TODO 1.4: Vytvořit Minimal Scenario Engine

**File:** `tests/e2e/framework/scenario_engine.py` (~250 řádků)

**Požadavky:**

```python
"""
Scenario Engine for E2E Testing

Defines and executes test scenarios.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum


class ScenarioType(Enum):
    """Types of test scenarios"""
    PROMPT_ENGINEERING = "prompt_engineering"
    TOOL_SELECTION = "tool_selection"
    CONTEXT_AWARENESS = "context_awareness"
    ERROR_HANDLING = "error_handling"
    MULTI_STEP = "multi_step"


@dataclass
class TestScenario:
    """
    Definition of a test scenario.

    Attributes:
        name: Scenario name
        type: Scenario type
        user_input: Input from user
        expected_tool: Expected tool to be selected
        expected_confidence: Minimum expected confidence
        context: Optional context for the scenario
        validation_rules: Custom validation functions
        description: Human-readable description
    """
    name: str
    type: ScenarioType
    user_input: str
    expected_tool: str
    expected_confidence: float = 0.7
    context: Optional[Dict[str, Any]] = None
    validation_rules: List[Callable] = field(default_factory=list)
    description: str = ""

    def __post_init__(self):
        """Validate scenario definition"""
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
        scenario: The executed scenario
        passed: Whether scenario passed
        actual_tool: Tool that was actually selected
        actual_confidence: Confidence of the selection
        failures: List of validation failures
        execution_time_ms: Time taken to execute
        metadata: Additional metadata
    """
    scenario: TestScenario
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
    - Run individual scenarios
    - Run scenario suites
    - Validate results against expectations
    - Collect metrics
    """

    def __init__(self, ai_simulator):
        """
        Initialize scenario engine.

        Args:
            ai_simulator: AI simulator instance to use for testing
        """
        self.simulator = ai_simulator
        self.results = []

    def execute_scenario(self, scenario: TestScenario) -> ScenarioResult:
        """
        Execute a single test scenario.

        Args:
            scenario: Scenario to execute

        Returns:
            ScenarioResult with execution details
        """
        import time

        start_time = time.time()

        # Execute simulation
        response = self.simulator.simulate(
            scenario.user_input,
            context=scenario.context
        )

        execution_time_ms = int((time.time() - start_time) * 1000)

        # Validate response
        failures = self._validate_response(scenario, response)
        passed = len(failures) == 0

        result = ScenarioResult(
            scenario=scenario,
            passed=passed,
            actual_tool=response.get("tool", "unknown"),
            actual_confidence=response.get("confidence", 0.0),
            failures=failures,
            execution_time_ms=execution_time_ms,
            metadata={"response": response}
        )

        self.results.append(result)
        return result

    def _validate_response(self, scenario: TestScenario, response: Dict[str, Any]) -> List[str]:
        """
        Validate AI response against scenario expectations.

        Args:
            scenario: Expected scenario
            response: Actual response from simulator

        Returns:
            List of validation failure messages (empty if all passed)
        """
        failures = []

        # Check tool selection
        actual_tool = response.get("tool")
        if actual_tool != scenario.expected_tool:
            failures.append(
                f"Tool mismatch: expected '{scenario.expected_tool}', got '{actual_tool}'"
            )

        # Check confidence
        actual_confidence = response.get("confidence", 0.0)
        if actual_confidence < scenario.expected_confidence:
            failures.append(
                f"Confidence too low: expected >= {scenario.expected_confidence}, "
                f"got {actual_confidence}"
            )

        # Run custom validation rules
        for rule in scenario.validation_rules:
            try:
                rule_result = rule(response)
                if not rule_result:
                    failures.append(f"Custom validation failed: {rule.__name__}")
            except Exception as e:
                failures.append(f"Custom validation error: {e}")

        return failures

    def execute_suite(self, scenarios: List[TestScenario]) -> List[ScenarioResult]:
        """
        Execute multiple scenarios.

        Args:
            scenarios: List of scenarios to execute

        Returns:
            List of scenario results
        """
        results = []
        for scenario in scenarios:
            result = self.execute_scenario(scenario)
            results.append(result)

        return results

    def get_pass_rate(self) -> float:
        """
        Calculate pass rate for executed scenarios.

        Returns:
            Pass rate as float 0-1
        """
        if not self.results:
            return 0.0

        passed = sum(1 for r in self.results if r.passed)
        return passed / len(self.results)

    def get_failures(self) -> List[ScenarioResult]:
        """Get all failed scenarios"""
        return [r for r in self.results if not r.passed]

    def reset(self):
        """Reset results"""
        self.results = []


# Predefined scenario library
COMMON_SCENARIOS = [
    TestScenario(
        name="simple_file_read",
        type=ScenarioType.TOOL_SELECTION,
        user_input="Read mycoder_config.json",
        expected_tool="file_read",
        expected_confidence=0.8,
        description="Basic file read operation"
    ),
    TestScenario(
        name="bash_command",
        type=ScenarioType.TOOL_SELECTION,
        user_input="Run pytest tests/",
        expected_tool="bash",
        expected_confidence=0.8,
        description="Basic command execution"
    ),
    TestScenario(
        name="multi_step_workflow",
        type=ScenarioType.MULTI_STEP,
        user_input="Update dependencies and run tests",
        expected_tool="multi_step",
        expected_confidence=0.7,
        description="Multi-step task requiring planning"
    ),
]


# TODO: Add more predefined scenarios
# TODO: Implement scenario loading from JSON/YAML
# TODO: Add scenario parameterization
```

---

### TODO 1.5: Spustit POC a ověřit funkcionalitu

```bash
# Run POC tests
poetry run pytest tests/e2e/test_poc_tool_selection.py -v

# Expected output:
# ✅ test_file_read_operations PASSED
# ✅ test_file_write_operations PASSED
# ✅ test_bash_command_execution PASSED
# ✅ test_multi_step_tasks PASSED
# ✅ test_ambiguous_requests PASSED
# ... etc

# Should have 15-20 tests passing
```

---

## FÁZE 2: Full Framework Implementation

### TODO 2.1: Assertion Framework

**File:** `tests/e2e/framework/assertion_framework.py` (~200 řádků)

**Features:**
- AI-specific assertions (tool_selected, context_retained, etc.)
- Custom failure messages
- Chaining assertions

**Example API:**
```python
from tests.e2e.framework.assertion_framework import AIAssertions

assertions = AIAssertions()

# Tool selection assertions
assertions.assert_tool_selected(response, "file_read")
assertions.assert_tool_confidence(response, min_confidence=0.8)

# Context assertions
assertions.assert_context_used(response, ["file_path", "working_dir"])
assertions.assert_context_retained(response, previous_context)

# Multi-step assertions
assertions.assert_multi_step(response, expected_steps=2)
assertions.assert_step_tool(response, step_index=0, expected_tool="file_read")

# Quality assertions
assertions.assert_response_quality(response, min_score=0.8)
assertions.assert_reasoning_present(response)
```

---

### TODO 2.2: Metrics Collector

**File:** `tests/e2e/framework/metrics_collector.py` (~180 řádků)

**Metrics to track:**
1. Tool Selection Accuracy (% correct tools)
2. Context Retention Rate (% context preserved)
3. Response Quality Score (0-1)
4. Error Recovery Rate (% recovered from errors)
5. Prompt Adherence Score (% followed instructions)
6. Execution Time (ms per scenario)

**API:**
```python
from tests.e2e.framework.metrics_collector import MetricsCollector

collector = MetricsCollector()

# Record metrics
collector.record_tool_selection(expected="file_read", actual="file_read", correct=True)
collector.record_context_retention(retained=True)
collector.record_execution_time(scenario_name="test_1", time_ms=45)

# Get aggregated metrics
metrics = collector.get_metrics()
# {
#   "tool_accuracy": 0.95,
#   "context_retention": 0.92,
#   "avg_execution_time_ms": 38,
#   ...
# }
```

---

### TODO 2.3: Comprehensive Test Scenarios

**Files:**
- `tests/e2e/test_ai_prompt_engineering.py` (~400 řádků)
- `tests/e2e/test_ai_tool_selection.py` (~350 řádků)
- `tests/e2e/test_ai_context_retention.py` (~300 řádků)
- `tests/e2e/test_ai_error_handling.py` (~250 řádků)

**Test Coverage:**
- ✅ 50+ scenarios covering common use cases
- ✅ Edge cases and corner cases
- ✅ Error scenarios and recovery
- ✅ Multi-turn conversations
- ✅ Complex multi-step workflows
- ✅ Thermal-aware tool selection
- ✅ Provider fallback scenarios

---

### TODO 2.4: Scenario Library (Fixtures)

**Files:**
- `tests/e2e/fixtures/mock_responses.json`
- `tests/e2e/fixtures/test_prompts.json`
- `tests/e2e/fixtures/expected_behaviors.json`

**Structure:**
```json
{
  "scenarios": [
    {
      "name": "read_config_file",
      "prompt": "Read mycoder_config.json",
      "expected_tool": "file_read",
      "confidence_min": 0.8,
      "context": {},
      "tags": ["file_ops", "common"]
    },
    {
      "name": "multi_step_update_test",
      "prompt": "Update dependencies and run tests",
      "expected_tool": "multi_step",
      "expected_steps": ["bash", "bash"],
      "tags": ["multi_step", "workflow"]
    }
  ]
}
```

---

## FÁZE 3: Automation & Self-Improvement

### TODO 3.1: Self-Test Runner

**File:** `tests/e2e/runner.py` (~400 řádků)

**Features:**
- Run all scenarios automatically
- Auto-iteration on failures
- Improvement suggestions
- Report generation

**CLI Usage:**
```bash
# Run all tests
poetry run python tests/e2e/runner.py

# Auto-iterate mode
poetry run python tests/e2e/runner.py --auto-iterate --max-iterations 10

# Generate report
poetry run python tests/e2e/runner.py --report

# Run specific scenario type
poetry run python tests/e2e/runner.py --scenario-type tool_selection
```

**Auto-Iteration Logic:**
```python
def auto_iterate(max_iterations=10, target_pass_rate=0.95):
    """
    Automatically iterate on test failures.

    Process:
    1. Run all scenarios
    2. Analyze failures
    3. Suggest improvements
    4. (Optional) Apply improvements automatically
    5. Re-run failed scenarios
    6. Repeat until target_pass_rate or max_iterations
    """
    for iteration in range(1, max_iterations + 1):
        results = run_all_scenarios()
        pass_rate = calculate_pass_rate(results)

        if pass_rate >= target_pass_rate:
            print(f"✅ Target achieved after {iteration} iterations!")
            break

        failures = get_failures(results)
        improvements = analyze_failures(failures)

        print(f"📊 Iteration {iteration}: {pass_rate*100:.1f}% passed")
        print(f"🔧 Applying {len(improvements)} improvements...")

        for improvement in improvements:
            apply_improvement(improvement)

        # Re-run failed scenarios
        rerun_results = rerun_scenarios(failures)
```

---

### TODO 3.2: Report Generator

**File:** `tests/e2e/framework/report_generator.py` (~250 řádků)

**Report Formats:**

1. **Console Output** (real-time)
```
🚀 AI Testing Framework - Test Run
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Scenarios Executed: 45
✅ Passed: 42 (93.3%)
❌ Failed: 3 (6.7%)

Metrics:
  Tool Accuracy: 95.6%
  Context Retention: 92.1%
  Avg Response Time: 38ms

Failed Scenarios:
  1. ambiguous_request_1 - Low confidence (0.45)
  2. context_long_term - Context lost after 5 turns
  3. thermal_aware_selection - Wrong provider selected
```

2. **JSON Report** (for parsing)
```json
{
  "run_id": "2026-01-14_21-30",
  "timestamp": "2026-01-14T21:30:00",
  "total_scenarios": 45,
  "passed": 42,
  "failed": 3,
  "pass_rate": 0.933,
  "metrics": {
    "tool_accuracy": 0.956,
    "context_retention": 0.921,
    "avg_time_ms": 38
  },
  "failures": [...]
}
```

3. **HTML Dashboard** (visualization)
```html
<!DOCTYPE html>
<html>
<head>
  <title>AI Test Results</title>
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
  <h1>AI Testing Dashboard</h1>
  <div id="pass-rate-chart"></div>
  <div id="metrics-table"></div>
  <!-- Interactive charts and tables -->
</body>
</html>
```

---

## TESTING STRATEGY

### Unit Tests (Framework Components)

```bash
# Test AI Simulator
poetry run pytest tests/e2e/framework/test_ai_simulator.py -v

# Test Scenario Engine
poetry run pytest tests/e2e/framework/test_scenario_engine.py -v

# Test Assertions
poetry run pytest tests/e2e/framework/test_assertion_framework.py -v
```

### Integration Tests

```bash
# Test complete E2E flow
poetry run pytest tests/e2e/test_e2e_integration.py -v
```

### POC Validation

```bash
# Quick POC test
poetry run pytest tests/e2e/test_poc_tool_selection.py -v

# Should complete in < 5 seconds
# Should have 15+ tests passing
```

---

## SUCCESS CRITERIA

### Fáze 1 (POC) ✅
- [ ] AI Simulator implementován a funguje
- [ ] 15+ POC testů passed
- [ ] Scenario Engine běží
- [ ] POC dokončen za < 2 hodiny

### Fáze 2 (Full Framework) ✅
- [ ] Assertion framework kompletní
- [ ] Metrics collector tracking všechny metriky
- [ ] 50+ test scenarios implemented
- [ ] Scenario library (JSON fixtures)
- [ ] Pass rate > 90% na core scenarios

### Fáze 3 (Automation) ✅
- [ ] Self-test runner funguje
- [ ] Auto-iteration mode implementován
- [ ] Report generator vytváří všechny formáty
- [ ] Integration s existing tests
- [ ] CI/CD ready

---

## DOCUMENTATION TODO

- [ ] Update `tests/e2e/AI_TESTING_FRAMEWORK.md` s aktuálním stavem
- [ ] Vytvořit `tests/e2e/README.md` s usage examples
- [ ] Přidat docstrings do všech classes
- [ ] Vytvořit example scripts v `tests/e2e/examples/`

---

## FINAL DELIVERABLES

Po dokončení implementace:

1. **Core Framework** (7 files)
   - `framework/ai_simulator.py`
   - `framework/scenario_engine.py`
   - `framework/assertion_framework.py`
   - `framework/metrics_collector.py`
   - `framework/report_generator.py`
   - `framework/__init__.py`
   - `runner.py`

2. **Test Suites** (5+ files)
   - `test_poc_tool_selection.py`
   - `test_ai_prompt_engineering.py`
   - `test_ai_tool_selection.py`
   - `test_ai_context_retention.py`
   - `test_ai_error_handling.py`

3. **Fixtures** (3 files)
   - `fixtures/mock_responses.json`
   - `fixtures/test_prompts.json`
   - `fixtures/expected_behaviors.json`

4. **Documentation** (3 files)
   - `AI_TESTING_FRAMEWORK.md` (updated)
   - `README.md` (new)
   - `USAGE_GUIDE.md` (new)

5. **Examples**
   - `examples/basic_usage.py`
   - `examples/auto_iteration.py`
   - `examples/custom_scenarios.py`

---

## NOTES & TIPS

### Pro Codex:

1. **Start s POC** - Implementuj Fázi 1 nejdřív, ověř že funguje
2. **Pattern matching** - AI Simulator používá regex a pattern matching
3. **Deterministic responses** - Důležité pro reprodukovatelné testy
4. **Test coverage** - Minimálně 50+ scenarios pro comprehensive testing
5. **Performance** - Celá test suite by měla běžet < 5 minut
6. **Documentation** - Každá class potřebuje docstring s examples
7. **Error handling** - Graceful handling všech edge cases

### Coding Style:

- Python 3.10-3.13 compatible
- Type hints všude
- Docstrings (Google style)
- Pytest conventions (test_*, Test*)
- Black formatting
- Import organization (isort)

### Testing:

Po každé fázi:
```bash
# Format
poetry run black tests/e2e/
poetry run isort tests/e2e/

# Lint
poetry run flake8 tests/e2e/

# Test
poetry run pytest tests/e2e/ -v
```

---

## QUESTIONS?

Pro referenci:
1. Čti `tests/e2e/AI_TESTING_FRAMEWORK.md` - Celková architektura
2. Čti `tests/e2e/IMPLEMENTATION_PLAN.md` - Detailní plán
3. Čti `tests/e2e/test_simulation.py` - Existující E2E test jako vzor
4. Prompt pattern matching - Použij regex pro flexibilitu
5. Test data - JSON fixtures pro škálovatelnost

**Implementace time estimate: 2-3 dny (Fáze 1: 2h, Fáze 2: 1 den, Fáze 3: 1 den)**

---

Good luck! 🚀

**Až dokončíš Fázi 1 (POC), pusť testy a dej vědět - můžeme pokračovat Fází 2!**
