# Model Router & Orchestrator (Triad System) - Implementation Spec

## Overview

**Module:** `src/mycoder/router/model_router.py`
**Purpose:** Intelligent LLM routing using the "Triad" strategy with budget awareness and FailureMemory integration

This document provides a step-by-step implementation guide for a Junior Developer to implement the "Model Router & Orchestrator" system.

---

## The Triad Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER PROMPT                                          │
│                    "Add authentication to the API"                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INTENT CLASSIFIER                                       │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│   │   SIMPLE    │  │   MEDIUM    │  │   COMPLEX   │  │   REVIEW    │       │
│   │  (Worker)   │  │  (Worker)   │  │ (Architect) │  │ (Reviewer)  │       │
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌───────────────────────┐ ┌───────────────────┐ ┌───────────────────────┐
│   🏛️ ARCHITECT        │ │   🔧 WORKER       │ │   🔍 REVIEWER         │
│   Claude Opus 4       │ │   GPT-4o / Codex  │ │   Gemini 1.5 Pro     │
│                       │ │   Claude Sonnet   │ │   Claude Sonnet      │
│   • Complex planning  │ │                   │ │                       │
│   • Refactoring       │ │   • Code writing  │ │   • Context review   │
│   • Hard debugging    │ │   • Boilerplate   │ │   • Impact analysis  │
│   • Architecture      │ │   • Patches       │ │   • Log analysis     │
│                       │ │   • Unit tests    │ │   • Final check      │
│   Cost: $$$$          │ │   Cost: $$        │ │   Cost: $$$          │
└───────────────────────┘ └───────────────────┘ └───────────────────────┘
            │                       │                       │
            └───────────────────────┼───────────────────────┘
                                    ▼
                    ┌───────────────────────────┐
                    │      TaskContext          │
                    │  (Passed between models)  │
                    └───────────────────────────┘
```

---

## Architecture

### Request Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ModelRouter                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   route_request(prompt, budget, context)                                    │
│         │                                                                    │
│         ▼                                                                    │
│   ┌─────────────────────────────────────────┐                               │
│   │  1. CLASSIFY INTENT                      │                               │
│   │     - Analyze prompt complexity          │                               │
│   │     - Detect keywords/patterns           │                               │
│   │     - Estimate token count               │                               │
│   │     - Return: TaskComplexity enum        │                               │
│   └─────────────────────────────────────────┘                               │
│         │                                                                    │
│         ▼                                                                    │
│   ┌─────────────────────────────────────────┐                               │
│   │  2. SELECT MODEL ROLE                    │                               │
│   │     - Apply budget constraints           │                               │
│   │     - Check FailureMemory warnings       │                               │
│   │     - Select: ARCHITECT/WORKER/REVIEWER  │                               │
│   └─────────────────────────────────────────┘                               │
│         │                                                                    │
│         ▼                                                                    │
│   ┌─────────────────────────────────────────┐                               │
│   │  3. INJECT CONSTRAINTS                   │                               │
│   │     - Add FailureMemory warnings         │                               │
│   │     - Add budget constraints             │                               │
│   │     - Add previous context               │                               │
│   └─────────────────────────────────────────┘                               │
│         │                                                                    │
│         ▼                                                                    │
│   ┌─────────────────────────────────────────┐                               │
│   │  4. EXECUTE WITH ADAPTER                 │                               │
│   │     - Call appropriate ModelAdapter      │                               │
│   │     - Handle streaming/non-streaming     │                               │
│   │     - Track costs                        │                               │
│   └─────────────────────────────────────────┘                               │
│         │                                                                    │
│         ▼                                                                    │
│   ┌─────────────────────────────────────────┐                               │
│   │  5. ORCHESTRATE HANDOFF (if needed)      │                               │
│   │     - Architect → Worker (plan to code)  │                               │
│   │     - Worker → Reviewer (code to review) │                               │
│   │     - Update TaskContext                 │                               │
│   └─────────────────────────────────────────┘                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
src/mycoder/router/
├── __init__.py              # NEW: Module exports
├── model_router.py          # NEW: Main ModelRouter class
├── intent_classifier.py     # NEW: Intent classification logic
├── task_context.py          # NEW: TaskContext dataclass
├── adapters/
│   ├── __init__.py          # NEW: Adapter exports
│   ├── base.py              # NEW: BaseModelAdapter ABC
│   ├── claude_adapter.py    # NEW: Claude (Opus/Sonnet) adapter
│   ├── openai_adapter.py    # NEW: OpenAI (GPT-4o/Codex) adapter
│   └── gemini_adapter.py    # NEW: Gemini adapter
└── budget.py                # NEW: Budget management

src/mycoder/
├── api_providers.py         # EXISTING: Keep for fallback system
├── tool_registry.py         # EXISTING: Integrate with router
└── self_evolve/
    └── failure_memory.py    # EXISTING: Integrate warnings
```

---

## Data Models

### Enums

```python
# src/mycoder/router/task_context.py

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime


class ModelRole(Enum):
    """The three model roles in the Triad system."""
    ARCHITECT = "architect"   # Claude Opus - complex planning
    WORKER = "worker"         # GPT-4o/Codex - code generation
    REVIEWER = "reviewer"     # Gemini 1.5 Pro - context review


class TaskComplexity(Enum):
    """Classified complexity of a task."""
    TRIVIAL = "trivial"       # One-liner fix, typo correction
    SIMPLE = "simple"         # Small function, single file change
    MEDIUM = "medium"         # Multiple files, some coordination
    COMPLEX = "complex"       # Architecture, refactoring, hard debug
    REVIEW = "review"         # Needs large context analysis


class BudgetTier(Enum):
    """Budget constraint tiers."""
    MINIMAL = "minimal"       # Only free/cheapest models (Haiku, local)
    LOW = "low"               # Prefer cheap (Sonnet, Flash)
    STANDARD = "standard"     # Balanced (Sonnet, GPT-4o)
    HIGH = "high"             # Allow expensive (Opus occasionally)
    UNLIMITED = "unlimited"   # Full access to Opus


class HandoffType(Enum):
    """Types of model handoffs."""
    PLAN_TO_CODE = "plan_to_code"           # Architect → Worker
    CODE_TO_REVIEW = "code_to_review"       # Worker → Reviewer
    REVIEW_TO_FIX = "review_to_fix"         # Reviewer → Worker
    ESCALATE = "escalate"                   # Worker → Architect (stuck)
```

### TaskContext

```python
@dataclass
class TaskContext:
    """
    Context passed between models during orchestration.

    This is the "baton" in the relay race - each model adds
    its contribution and passes it to the next.
    """

    # Original request
    original_prompt: str
    user_intent: str = ""

    # Classification
    complexity: TaskComplexity = TaskComplexity.MEDIUM
    estimated_tokens: int = 0

    # Budget
    budget_tier: BudgetTier = BudgetTier.STANDARD
    budget_remaining_usd: float = 10.0
    cost_so_far_usd: float = 0.0

    # Execution history
    execution_history: List[Dict[str, Any]] = field(default_factory=list)
    current_role: Optional[ModelRole] = None

    # Architect outputs
    plan: Optional[str] = None
    plan_steps: List[str] = field(default_factory=list)
    architecture_notes: Optional[str] = None

    # Worker outputs
    generated_code: Dict[str, str] = field(default_factory=dict)  # filepath -> code
    patches: List[str] = field(default_factory=list)

    # Reviewer outputs
    review_result: Optional[str] = None
    review_passed: bool = False
    review_issues: List[str] = field(default_factory=list)

    # Failure Memory integration
    failure_warnings: List[str] = field(default_factory=list)
    blocked_patterns: List[str] = field(default_factory=list)

    # File context (for Reviewer's large context)
    file_context: Dict[str, str] = field(default_factory=dict)  # filepath -> content

    # Metadata
    session_id: str = ""
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_execution(
        self,
        role: ModelRole,
        model_name: str,
        prompt: str,
        response: str,
        cost_usd: float,
        duration_ms: int,
    ) -> None:
        """Record an execution step."""
        self.execution_history.append({
            "role": role.value,
            "model": model_name,
            "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
            "response_preview": response[:500] + "..." if len(response) > 500 else response,
            "cost_usd": cost_usd,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
        })
        self.cost_so_far_usd += cost_usd
        self.budget_remaining_usd -= cost_usd

    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary."""
        return {
            "original_prompt": self.original_prompt[:100],
            "complexity": self.complexity.value,
            "total_cost_usd": self.cost_so_far_usd,
            "execution_steps": len(self.execution_history),
            "review_passed": self.review_passed,
            "files_modified": list(self.generated_code.keys()),
        }
```

### RouterResult

```python
@dataclass
class RouterResult:
    """Result from ModelRouter.route_request()."""

    success: bool
    content: str

    # What was used
    model_role: ModelRole
    model_name: str

    # Costs
    cost_usd: float
    duration_ms: int
    tokens_used: int

    # Context (for chaining)
    task_context: TaskContext

    # Handoff info
    requires_handoff: bool = False
    next_role: Optional[ModelRole] = None
    handoff_prompt: Optional[str] = None

    # Errors
    error: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

## Base Model Adapter Interface

```python
# src/mycoder/router/adapters/base.py

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class ModelCapability(Enum):
    """Capabilities a model might have."""
    PLANNING = "planning"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    LARGE_CONTEXT = "large_context"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"
    VISION = "vision"


@dataclass
class ModelInfo:
    """Information about a model."""
    name: str
    provider: str  # "anthropic", "openai", "google"

    # Costs (per 1M tokens)
    input_cost_per_mtok: float
    output_cost_per_mtok: float

    # Limits
    max_context_tokens: int
    max_output_tokens: int

    # Capabilities
    capabilities: List[ModelCapability]

    # Performance hints
    typical_latency_ms: int  # First token latency
    tokens_per_second: int   # Output speed

    # Role suitability (0.0 - 1.0)
    architect_score: float = 0.0
    worker_score: float = 0.0
    reviewer_score: float = 0.0


@dataclass
class AdapterResponse:
    """Response from a model adapter."""
    success: bool
    content: str
    model_name: str

    # Token usage
    input_tokens: int
    output_tokens: int

    # Cost
    cost_usd: float

    # Timing
    duration_ms: int
    time_to_first_token_ms: Optional[int] = None

    # Metadata
    finish_reason: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class BaseModelAdapter(ABC):
    """
    Abstract base class for model adapters.

    Each adapter wraps a specific LLM provider and normalizes
    the interface for the ModelRouter.
    """

    def __init__(self, model_info: ModelInfo):
        self.model_info = model_info
        self.is_initialized = False

    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the adapter (check API keys, warm up connections).
        Returns True if ready to use.
        """
        pass

    @abstractmethod
    async def query(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[TaskContext] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> AdapterResponse:
        """
        Execute a query against the model.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt (injected constraints)
            context: TaskContext for additional context
            stream_callback: Callback for streaming responses
            max_tokens: Max output tokens (uses model default if None)
            temperature: Sampling temperature
            **kwargs: Provider-specific options

        Returns:
            AdapterResponse with results
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the adapter is healthy and ready."""
        pass

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a query."""
        input_cost = (input_tokens / 1_000_000) * self.model_info.input_cost_per_mtok
        output_cost = (output_tokens / 1_000_000) * self.model_info.output_cost_per_mtok
        return input_cost + output_cost

    def can_handle_tokens(self, estimated_tokens: int) -> bool:
        """Check if model can handle the estimated token count."""
        return estimated_tokens <= self.model_info.max_context_tokens

    def get_role_score(self, role: "ModelRole") -> float:
        """Get suitability score for a role."""
        from ..task_context import ModelRole
        scores = {
            ModelRole.ARCHITECT: self.model_info.architect_score,
            ModelRole.WORKER: self.model_info.worker_score,
            ModelRole.REVIEWER: self.model_info.reviewer_score,
        }
        return scores.get(role, 0.0)
```

---

## Model Configurations

```python
# src/mycoder/router/adapters/__init__.py

from .base import ModelInfo, ModelCapability

# ============================================================================
# ARCHITECT MODELS (High intelligence, complex reasoning)
# ============================================================================

CLAUDE_OPUS_4 = ModelInfo(
    name="claude-opus-4-20250514",
    provider="anthropic",
    input_cost_per_mtok=15.0,
    output_cost_per_mtok=75.0,
    max_context_tokens=200_000,
    max_output_tokens=32_000,
    capabilities=[
        ModelCapability.PLANNING,
        ModelCapability.CODE_GENERATION,
        ModelCapability.CODE_REVIEW,
        ModelCapability.LARGE_CONTEXT,
        ModelCapability.FUNCTION_CALLING,
        ModelCapability.STREAMING,
    ],
    typical_latency_ms=2000,
    tokens_per_second=50,
    architect_score=1.0,
    worker_score=0.7,
    reviewer_score=0.8,
)

CLAUDE_SONNET_4 = ModelInfo(
    name="claude-sonnet-4-20250514",
    provider="anthropic",
    input_cost_per_mtok=3.0,
    output_cost_per_mtok=15.0,
    max_context_tokens=200_000,
    max_output_tokens=64_000,
    capabilities=[
        ModelCapability.PLANNING,
        ModelCapability.CODE_GENERATION,
        ModelCapability.CODE_REVIEW,
        ModelCapability.LARGE_CONTEXT,
        ModelCapability.FUNCTION_CALLING,
        ModelCapability.STREAMING,
    ],
    typical_latency_ms=800,
    tokens_per_second=100,
    architect_score=0.7,
    worker_score=0.9,
    reviewer_score=0.8,
)

# ============================================================================
# WORKER MODELS (Fast code generation)
# ============================================================================

GPT_4O = ModelInfo(
    name="gpt-4o",
    provider="openai",
    input_cost_per_mtok=2.5,
    output_cost_per_mtok=10.0,
    max_context_tokens=128_000,
    max_output_tokens=16_384,
    capabilities=[
        ModelCapability.CODE_GENERATION,
        ModelCapability.CODE_REVIEW,
        ModelCapability.FUNCTION_CALLING,
        ModelCapability.STREAMING,
        ModelCapability.VISION,
    ],
    typical_latency_ms=500,
    tokens_per_second=150,
    architect_score=0.6,
    worker_score=0.95,
    reviewer_score=0.7,
)

GPT_4O_MINI = ModelInfo(
    name="gpt-4o-mini",
    provider="openai",
    input_cost_per_mtok=0.15,
    output_cost_per_mtok=0.6,
    max_context_tokens=128_000,
    max_output_tokens=16_384,
    capabilities=[
        ModelCapability.CODE_GENERATION,
        ModelCapability.STREAMING,
        ModelCapability.VISION,
    ],
    typical_latency_ms=300,
    tokens_per_second=200,
    architect_score=0.3,
    worker_score=0.7,
    reviewer_score=0.5,
)

CLAUDE_HAIKU = ModelInfo(
    name="claude-3-5-haiku-20241022",
    provider="anthropic",
    input_cost_per_mtok=0.8,
    output_cost_per_mtok=4.0,
    max_context_tokens=200_000,
    max_output_tokens=8_192,
    capabilities=[
        ModelCapability.CODE_GENERATION,
        ModelCapability.STREAMING,
    ],
    typical_latency_ms=200,
    tokens_per_second=250,
    architect_score=0.2,
    worker_score=0.6,
    reviewer_score=0.4,
)

# ============================================================================
# REVIEWER MODELS (Large context window)
# ============================================================================

GEMINI_2_FLASH = ModelInfo(
    name="gemini-2.0-flash",
    provider="google",
    input_cost_per_mtok=0.1,
    output_cost_per_mtok=0.4,
    max_context_tokens=1_000_000,
    max_output_tokens=8_192,
    capabilities=[
        ModelCapability.CODE_REVIEW,
        ModelCapability.LARGE_CONTEXT,
        ModelCapability.STREAMING,
    ],
    typical_latency_ms=400,
    tokens_per_second=180,
    architect_score=0.4,
    worker_score=0.5,
    reviewer_score=0.95,
)

GEMINI_1_5_PRO = ModelInfo(
    name="gemini-1.5-pro",
    provider="google",
    input_cost_per_mtok=1.25,
    output_cost_per_mtok=5.0,
    max_context_tokens=2_000_000,
    max_output_tokens=8_192,
    capabilities=[
        ModelCapability.PLANNING,
        ModelCapability.CODE_REVIEW,
        ModelCapability.LARGE_CONTEXT,
        ModelCapability.STREAMING,
    ],
    typical_latency_ms=600,
    tokens_per_second=120,
    architect_score=0.5,
    worker_score=0.6,
    reviewer_score=1.0,
)


# Budget tier to model mapping
BUDGET_MODEL_MAP = {
    BudgetTier.MINIMAL: {
        ModelRole.ARCHITECT: CLAUDE_HAIKU,
        ModelRole.WORKER: GPT_4O_MINI,
        ModelRole.REVIEWER: GEMINI_2_FLASH,
    },
    BudgetTier.LOW: {
        ModelRole.ARCHITECT: CLAUDE_SONNET_4,
        ModelRole.WORKER: GPT_4O_MINI,
        ModelRole.REVIEWER: GEMINI_2_FLASH,
    },
    BudgetTier.STANDARD: {
        ModelRole.ARCHITECT: CLAUDE_SONNET_4,
        ModelRole.WORKER: GPT_4O,
        ModelRole.REVIEWER: GEMINI_2_FLASH,
    },
    BudgetTier.HIGH: {
        ModelRole.ARCHITECT: CLAUDE_OPUS_4,
        ModelRole.WORKER: CLAUDE_SONNET_4,
        ModelRole.REVIEWER: GEMINI_1_5_PRO,
    },
    BudgetTier.UNLIMITED: {
        ModelRole.ARCHITECT: CLAUDE_OPUS_4,
        ModelRole.WORKER: CLAUDE_SONNET_4,
        ModelRole.REVIEWER: GEMINI_1_5_PRO,
    },
}
```

---

## Intent Classifier

```python
# src/mycoder/router/intent_classifier.py

"""
Intent classification for determining task complexity and model routing.
"""

import re
from dataclasses import dataclass
from typing import List, Tuple

from .task_context import TaskComplexity


@dataclass
class ClassificationResult:
    """Result of intent classification."""
    complexity: TaskComplexity
    confidence: float  # 0.0 - 1.0
    reasons: List[str]
    estimated_tokens: int
    suggested_steps: List[str]


class IntentClassifier:
    """
    Classifies user prompts to determine task complexity.

    Uses heuristics + optional LLM for ambiguous cases.
    """

    # Patterns that suggest COMPLEX tasks (need Architect)
    COMPLEX_PATTERNS = [
        (r"\b(refactor|restructure|redesign|architect)\b", "Refactoring detected"),
        (r"\b(migrate|migration)\b", "Migration detected"),
        (r"\b(optimize|performance|bottleneck)\b", "Optimization detected"),
        (r"\b(security|vulnerability|auth|authentication)\b", "Security-related"),
        (r"\b(design pattern|architecture|system design)\b", "Architecture design"),
        (r"\bmulti[- ]?(file|module|service)\b", "Multi-component change"),
        (r"\b(debug|investigate|diagnose|why)\b.*\b(crash|fail|error|bug)\b", "Complex debugging"),
        (r"\b(implement|create|build)\b.*\b(feature|system|module)\b", "Feature implementation"),
    ]

    # Patterns that suggest SIMPLE tasks (Worker can handle)
    SIMPLE_PATTERNS = [
        (r"\b(fix|correct)\b.*\b(typo|spelling|whitespace)\b", "Typo fix"),
        (r"\b(add|insert)\b.*\b(comment|docstring|log)\b", "Add documentation"),
        (r"\b(rename|change name)\b", "Simple rename"),
        (r"\b(update|change)\b.*\b(version|constant|config)\b", "Config update"),
        (r"\bformat\b.*\bcode\b", "Code formatting"),
    ]

    # Patterns that suggest REVIEW tasks (need Reviewer)
    REVIEW_PATTERNS = [
        (r"\b(review|check|analyze|audit)\b", "Review requested"),
        (r"\b(impact|affect|break|regression)\b", "Impact analysis"),
        (r"\b(all files|entire|whole|codebase)\b", "Large scope"),
        (r"\b(log|logs|output|trace)\b.*\b(analyze|check|find)\b", "Log analysis"),
    ]

    # Token estimation heuristics
    TOKENS_PER_FILE = 500  # Average tokens per file mentioned
    TOKENS_PER_FUNCTION = 100  # Average tokens per function
    BASE_PROMPT_TOKENS = 200  # Base overhead

    def classify(self, prompt: str, file_context: List[str] = None) -> ClassificationResult:
        """
        Classify the intent and complexity of a prompt.

        Args:
            prompt: User's input prompt
            file_context: List of file paths in context

        Returns:
            ClassificationResult with complexity and reasoning
        """
        prompt_lower = prompt.lower()
        reasons = []

        # Check for COMPLEX patterns
        complex_score = 0
        for pattern, reason in self.COMPLEX_PATTERNS:
            if re.search(pattern, prompt_lower):
                complex_score += 1
                reasons.append(f"[COMPLEX] {reason}")

        # Check for SIMPLE patterns
        simple_score = 0
        for pattern, reason in self.SIMPLE_PATTERNS:
            if re.search(pattern, prompt_lower):
                simple_score += 1
                reasons.append(f"[SIMPLE] {reason}")

        # Check for REVIEW patterns
        review_score = 0
        for pattern, reason in self.REVIEW_PATTERNS:
            if re.search(pattern, prompt_lower):
                review_score += 1
                reasons.append(f"[REVIEW] {reason}")

        # Estimate tokens
        estimated_tokens = self._estimate_tokens(prompt, file_context)

        # Large context needs Reviewer
        if estimated_tokens > 50000:
            review_score += 2
            reasons.append(f"[REVIEW] Large context: ~{estimated_tokens} tokens")

        # Determine complexity
        complexity, confidence = self._determine_complexity(
            complex_score, simple_score, review_score, len(prompt)
        )

        # Generate suggested steps
        suggested_steps = self._generate_steps(complexity, prompt)

        return ClassificationResult(
            complexity=complexity,
            confidence=confidence,
            reasons=reasons if reasons else ["No specific patterns detected"],
            estimated_tokens=estimated_tokens,
            suggested_steps=suggested_steps,
        )

    def _estimate_tokens(self, prompt: str, file_context: List[str] = None) -> int:
        """Estimate total tokens for the task."""
        # Prompt tokens (rough: 4 chars per token)
        prompt_tokens = len(prompt) // 4

        # File context tokens
        file_tokens = 0
        if file_context:
            file_tokens = len(file_context) * self.TOKENS_PER_FILE

        return self.BASE_PROMPT_TOKENS + prompt_tokens + file_tokens

    def _determine_complexity(
        self,
        complex_score: int,
        simple_score: int,
        review_score: int,
        prompt_length: int,
    ) -> Tuple[TaskComplexity, float]:
        """Determine complexity from scores."""

        # Review takes precedence if high
        if review_score >= 2:
            return TaskComplexity.REVIEW, 0.8

        # Complex takes precedence over simple
        if complex_score >= 2:
            return TaskComplexity.COMPLEX, 0.85
        if complex_score == 1 and simple_score == 0:
            return TaskComplexity.COMPLEX, 0.7

        # Simple
        if simple_score >= 2:
            return TaskComplexity.TRIVIAL, 0.9
        if simple_score == 1 and complex_score == 0:
            return TaskComplexity.SIMPLE, 0.75

        # Default based on length
        if prompt_length < 50:
            return TaskComplexity.SIMPLE, 0.5
        elif prompt_length < 200:
            return TaskComplexity.MEDIUM, 0.5
        else:
            return TaskComplexity.COMPLEX, 0.5

    def _generate_steps(self, complexity: TaskComplexity, prompt: str) -> List[str]:
        """Generate suggested execution steps."""
        if complexity == TaskComplexity.TRIVIAL:
            return ["Apply fix directly"]

        if complexity == TaskComplexity.SIMPLE:
            return [
                "Identify target file(s)",
                "Generate code change",
                "Apply patch",
            ]

        if complexity == TaskComplexity.MEDIUM:
            return [
                "Analyze affected files",
                "Plan changes",
                "Generate code for each file",
                "Review for consistency",
            ]

        if complexity == TaskComplexity.COMPLEX:
            return [
                "Architect: Analyze requirements",
                "Architect: Design solution",
                "Architect: Create implementation plan",
                "Worker: Implement each step",
                "Reviewer: Verify changes",
                "Reviewer: Check for regressions",
            ]

        if complexity == TaskComplexity.REVIEW:
            return [
                "Load full context",
                "Reviewer: Analyze codebase",
                "Reviewer: Generate report",
            ]

        return ["Process request"]
```

---

## ModelRouter - Main Class

```python
# src/mycoder/router/model_router.py

"""
Model Router & Orchestrator for MyCoder v2.2.0

Implements the Triad strategy:
- Architect (Opus): Complex planning
- Worker (GPT-4o/Sonnet): Code generation
- Reviewer (Gemini): Large context review
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from ..self_evolve.failure_memory import Advisory, AdvisoryResult, FailureMemory
from ..tool_registry import ToolRegistry
from .adapters import BUDGET_MODEL_MAP
from .adapters.base import AdapterResponse, BaseModelAdapter
from .intent_classifier import IntentClassifier
from .task_context import (
    BudgetTier,
    HandoffType,
    ModelRole,
    RouterResult,
    TaskComplexity,
    TaskContext,
)

logger = logging.getLogger(__name__)


class ModelRouter:
    """
    Intelligent model router implementing the Triad strategy.

    Routes requests to appropriate models based on:
    - Task complexity (intent classification)
    - Budget constraints
    - FailureMemory warnings
    - Model capabilities
    """

    # Complexity to primary role mapping
    COMPLEXITY_ROLE_MAP = {
        TaskComplexity.TRIVIAL: ModelRole.WORKER,
        TaskComplexity.SIMPLE: ModelRole.WORKER,
        TaskComplexity.MEDIUM: ModelRole.WORKER,
        TaskComplexity.COMPLEX: ModelRole.ARCHITECT,
        TaskComplexity.REVIEW: ModelRole.REVIEWER,
    }

    def __init__(
        self,
        failure_memory: Optional[FailureMemory] = None,
        tool_registry: Optional[ToolRegistry] = None,
        default_budget: BudgetTier = BudgetTier.STANDARD,
    ):
        self.failure_memory = failure_memory or FailureMemory()
        self.tool_registry = tool_registry
        self.default_budget = default_budget

        self.classifier = IntentClassifier()
        self.adapters: Dict[str, BaseModelAdapter] = {}

        # Statistics
        self.total_requests = 0
        self.total_cost_usd = 0.0
        self.requests_by_role: Dict[ModelRole, int] = {
            ModelRole.ARCHITECT: 0,
            ModelRole.WORKER: 0,
            ModelRole.REVIEWER: 0,
        }

    async def initialize_adapters(self) -> None:
        """Initialize all model adapters."""
        # Import adapters (lazy to avoid circular imports)
        from .adapters.claude_adapter import ClaudeAdapter
        from .adapters.gemini_adapter import GeminiAdapter
        from .adapters.openai_adapter import OpenAIAdapter

        # Initialize each adapter
        for model_info in BUDGET_MODEL_MAP[BudgetTier.UNLIMITED].values():
            if model_info.provider == "anthropic":
                adapter = ClaudeAdapter(model_info)
            elif model_info.provider == "openai":
                adapter = OpenAIAdapter(model_info)
            elif model_info.provider == "google":
                adapter = GeminiAdapter(model_info)
            else:
                continue

            if await adapter.initialize():
                self.adapters[model_info.name] = adapter
                logger.info(f"Initialized adapter: {model_info.name}")

    # ========================================================================
    # Main Routing API
    # ========================================================================

    async def route_request(
        self,
        prompt: str,
        budget: Optional[BudgetTier] = None,
        context: Optional[TaskContext] = None,
        file_context: Optional[List[str]] = None,
        stream_callback: Optional[Callable[[str], None]] = None,
        force_role: Optional[ModelRole] = None,
    ) -> RouterResult:
        """
        Route a request to the appropriate model.

        Args:
            prompt: User's input prompt
            budget: Budget tier (uses default if None)
            context: Existing TaskContext (for chained calls)
            file_context: List of file paths for context
            stream_callback: Callback for streaming responses
            force_role: Force a specific role (bypass classification)

        Returns:
            RouterResult with response and updated context
        """
        self.total_requests += 1
        budget = budget or self.default_budget

        # Create or update context
        if context is None:
            context = TaskContext(
                original_prompt=prompt,
                budget_tier=budget,
            )

        # Step 1: Classify intent
        classification = self.classifier.classify(prompt, file_context)
        context.complexity = classification.complexity
        context.estimated_tokens = classification.estimated_tokens

        logger.info(
            f"Classified intent: {classification.complexity.value} "
            f"(confidence: {classification.confidence:.0%})"
        )

        # Step 2: Select model role
        role = force_role or self.COMPLEXITY_ROLE_MAP[classification.complexity]
        context.current_role = role
        self.requests_by_role[role] += 1

        # Step 3: Get FailureMemory warnings and inject constraints
        system_prompt = await self._build_system_prompt(prompt, context, role)

        # Step 4: Select adapter based on budget and role
        adapter = self._select_adapter(role, budget, context)
        if not adapter:
            return RouterResult(
                success=False,
                content="",
                model_role=role,
                model_name="none",
                cost_usd=0.0,
                duration_ms=0,
                tokens_used=0,
                task_context=context,
                error=f"No adapter available for role {role.value} with budget {budget.value}",
            )

        # Step 5: Execute query
        response = await adapter.query(
            prompt=prompt,
            system_prompt=system_prompt,
            context=context,
            stream_callback=stream_callback,
        )

        # Update context
        context.add_execution(
            role=role,
            model_name=adapter.model_info.name,
            prompt=prompt,
            response=response.content,
            cost_usd=response.cost_usd,
            duration_ms=response.duration_ms,
        )

        self.total_cost_usd += response.cost_usd

        # Step 6: Determine if handoff is needed
        requires_handoff, next_role, handoff_prompt = self._check_handoff(
            role, response, context, classification
        )

        return RouterResult(
            success=response.success,
            content=response.content,
            model_role=role,
            model_name=adapter.model_info.name,
            cost_usd=response.cost_usd,
            duration_ms=response.duration_ms,
            tokens_used=response.input_tokens + response.output_tokens,
            task_context=context,
            requires_handoff=requires_handoff,
            next_role=next_role,
            handoff_prompt=handoff_prompt,
            error=response.error,
        )

    async def orchestrate_full_task(
        self,
        prompt: str,
        budget: Optional[BudgetTier] = None,
        max_handoffs: int = 3,
        stream_callback: Optional[Callable[[str], None]] = None,
    ) -> RouterResult:
        """
        Orchestrate a full task with automatic handoffs.

        This is the high-level API that handles the complete
        Architect → Worker → Reviewer flow automatically.

        Args:
            prompt: User's input prompt
            budget: Budget tier
            max_handoffs: Maximum number of model handoffs
            stream_callback: Callback for streaming

        Returns:
            Final RouterResult after all handoffs
        """
        context = TaskContext(
            original_prompt=prompt,
            budget_tier=budget or self.default_budget,
        )

        current_prompt = prompt
        handoff_count = 0

        while handoff_count < max_handoffs:
            result = await self.route_request(
                prompt=current_prompt,
                budget=budget,
                context=context,
                stream_callback=stream_callback,
            )

            if not result.success:
                return result

            if not result.requires_handoff:
                return result

            # Prepare for handoff
            logger.info(
                f"Handoff {handoff_count + 1}: "
                f"{result.model_role.value} → {result.next_role.value}"
            )

            current_prompt = result.handoff_prompt or result.content
            handoff_count += 1

        logger.warning(f"Max handoffs ({max_handoffs}) reached")
        return result

    # ========================================================================
    # Internal Methods
    # ========================================================================

    async def _build_system_prompt(
        self,
        prompt: str,
        context: TaskContext,
        role: ModelRole,
    ) -> str:
        """Build system prompt with constraints from FailureMemory."""

        parts = []

        # Role-specific instructions
        if role == ModelRole.ARCHITECT:
            parts.append(
                "You are the ARCHITECT. Your role is to:\n"
                "- Analyze complex requirements\n"
                "- Design solutions and patterns\n"
                "- Create detailed implementation plans\n"
                "- Make architectural decisions\n"
                "Do NOT write implementation code. Focus on planning."
            )
        elif role == ModelRole.WORKER:
            parts.append(
                "You are the WORKER. Your role is to:\n"
                "- Write clean, tested code\n"
                "- Follow the plan provided (if any)\n"
                "- Generate complete, working implementations\n"
                "- Create patches that can be applied directly\n"
                "Focus on code quality and correctness."
            )
        elif role == ModelRole.REVIEWER:
            parts.append(
                "You are the REVIEWER. Your role is to:\n"
                "- Analyze code changes for correctness\n"
                "- Check for regressions and side effects\n"
                "- Review large contexts thoroughly\n"
                "- Identify potential issues\n"
                "Provide detailed, actionable feedback."
            )

        # Add plan context if available (Worker needs this)
        if role == ModelRole.WORKER and context.plan:
            parts.append(f"\n## Implementation Plan\n{context.plan}")

        # Inject FailureMemory warnings
        if self.failure_memory and context.failure_warnings:
            constraints = "\n## CONSTRAINTS (from previous failures)\n"
            for warning in context.failure_warnings:
                constraints += f"- {warning}\n"
            parts.append(constraints)

        # Check current tool/pattern failures
        advisory = self.failure_memory.check_advisory(
            tool_name="model_router",
            params={"prompt_hash": hash(prompt) % 10000},
        )

        if advisory.result in [AdvisoryResult.WARN, AdvisoryResult.BLOCK]:
            parts.append(
                f"\n## WARNING\nPrevious similar request failed: {advisory.reason}\n"
                "Consider a different approach."
            )

        # Budget reminder
        if context.budget_tier in [BudgetTier.MINIMAL, BudgetTier.LOW]:
            parts.append(
                "\n## Budget Constraint\n"
                "Keep responses concise. Avoid unnecessary elaboration."
            )

        return "\n\n".join(parts)

    def _select_adapter(
        self,
        role: ModelRole,
        budget: BudgetTier,
        context: TaskContext,
    ) -> Optional[BaseModelAdapter]:
        """Select the best adapter for the role and budget."""

        # Get model info for this budget/role combination
        model_info = BUDGET_MODEL_MAP.get(budget, {}).get(role)
        if not model_info:
            logger.error(f"No model configured for {budget.value}/{role.value}")
            return None

        # Get adapter
        adapter = self.adapters.get(model_info.name)
        if not adapter:
            # Try fallback to a lower budget tier
            for fallback_budget in [BudgetTier.STANDARD, BudgetTier.LOW, BudgetTier.MINIMAL]:
                fallback_info = BUDGET_MODEL_MAP.get(fallback_budget, {}).get(role)
                if fallback_info and fallback_info.name in self.adapters:
                    logger.warning(
                        f"Falling back from {model_info.name} to {fallback_info.name}"
                    )
                    return self.adapters[fallback_info.name]

        return adapter

    def _check_handoff(
        self,
        current_role: ModelRole,
        response: AdapterResponse,
        context: TaskContext,
        classification: "ClassificationResult",
    ) -> tuple:
        """
        Check if a handoff to another model is needed.

        Returns:
            (requires_handoff, next_role, handoff_prompt)
        """

        # Architect → Worker handoff
        if current_role == ModelRole.ARCHITECT:
            # Extract plan from response
            context.plan = response.content

            # Check if plan is complete enough to hand off
            if "implement" in response.content.lower() or "step" in response.content.lower():
                handoff_prompt = (
                    f"## Task\n{context.original_prompt}\n\n"
                    f"## Implementation Plan\n{response.content}\n\n"
                    "Implement the plan above. Generate complete, working code."
                )
                return True, ModelRole.WORKER, handoff_prompt

        # Worker → Reviewer handoff (for complex tasks)
        if current_role == ModelRole.WORKER:
            if classification.complexity in [TaskComplexity.COMPLEX, TaskComplexity.MEDIUM]:
                # Extract code from response
                context.patches.append(response.content)

                handoff_prompt = (
                    f"## Original Request\n{context.original_prompt}\n\n"
                    f"## Generated Code\n{response.content}\n\n"
                    "Review the code above for:\n"
                    "1. Correctness and completeness\n"
                    "2. Potential bugs or edge cases\n"
                    "3. Impact on other parts of the codebase\n"
                    "4. Security concerns"
                )
                return True, ModelRole.REVIEWER, handoff_prompt

        # Reviewer complete - no further handoff
        if current_role == ModelRole.REVIEWER:
            context.review_result = response.content
            context.review_passed = "approved" in response.content.lower() or \
                                   "lgtm" in response.content.lower()

        return False, None, None

    # ========================================================================
    # Statistics
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get router statistics."""
        return {
            "total_requests": self.total_requests,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "requests_by_role": {
                role.value: count
                for role, count in self.requests_by_role.items()
            },
            "adapters_available": list(self.adapters.keys()),
        }
```

---

## Integration Points

### With ToolRegistry

```python
# In src/mycoder/tool_registry.py, add to ToolRegistry.__init__:

from .router.model_router import ModelRouter

class ToolRegistry:
    def __init__(self):
        # ... existing code ...
        self.model_router: Optional[ModelRouter] = None

    def set_model_router(self, router: ModelRouter) -> None:
        """Set the model router for intelligent tool suggestions."""
        self.model_router = router
```

### With FailureMemory

The ModelRouter already integrates with FailureMemory:
1. Queries for warnings before execution
2. Injects constraints into system prompts
3. Can record failures for pattern-based blocking

---

## Implementation Steps (ToDo List for Codex)

### Phase 1: Data Structures (30 min)

1. **Create** directory: `src/mycoder/router/`
2. **Create** `src/mycoder/router/__init__.py` with basic exports
3. **Create** `src/mycoder/router/task_context.py`
4. **Add** enums: `ModelRole`, `TaskComplexity`, `BudgetTier`, `HandoffType`
5. **Add** `TaskContext` dataclass with all fields
6. **Add** `RouterResult` dataclass
7. **Run** formatter: `poetry run black src/mycoder/router/`

### Phase 2: Adapters Base (45 min)

8. **Create** `src/mycoder/router/adapters/` directory
9. **Create** `src/mycoder/router/adapters/__init__.py`
10. **Add** `ModelCapability` enum
11. **Add** `ModelInfo` dataclass
12. **Add** `AdapterResponse` dataclass
13. **Create** `src/mycoder/router/adapters/base.py`
14. **Implement** `BaseModelAdapter` ABC with abstract methods
15. **Add** `estimate_cost()` and `can_handle_tokens()` methods
16. **Add** model configurations (CLAUDE_OPUS_4, GPT_4O, GEMINI_2_FLASH, etc.)
17. **Add** `BUDGET_MODEL_MAP` dictionary

### Phase 3: Intent Classifier (30 min)

18. **Create** `src/mycoder/router/intent_classifier.py`
19. **Add** `ClassificationResult` dataclass
20. **Implement** `IntentClassifier` class
21. **Add** `COMPLEX_PATTERNS`, `SIMPLE_PATTERNS`, `REVIEW_PATTERNS`
22. **Implement** `classify()` method
23. **Implement** `_estimate_tokens()` method
24. **Implement** `_determine_complexity()` method
25. **Implement** `_generate_steps()` method

### Phase 4: Model Adapters (60 min)

26. **Create** `src/mycoder/router/adapters/claude_adapter.py`
27. **Implement** `ClaudeAdapter(BaseModelAdapter)`
28. **Implement** `initialize()`, `query()`, `health_check()` methods
29. **Create** `src/mycoder/router/adapters/openai_adapter.py`
30. **Implement** `OpenAIAdapter(BaseModelAdapter)`
31. **Create** `src/mycoder/router/adapters/gemini_adapter.py`
32. **Implement** `GeminiAdapter(BaseModelAdapter)`

### Phase 5: ModelRouter Core (60 min)

33. **Create** `src/mycoder/router/model_router.py`
34. **Add** imports and `COMPLEXITY_ROLE_MAP`
35. **Implement** `ModelRouter.__init__()`
36. **Implement** `initialize_adapters()` method
37. **Implement** `route_request()` method
38. **Implement** `orchestrate_full_task()` method
39. **Implement** `_build_system_prompt()` with FailureMemory integration
40. **Implement** `_select_adapter()` with budget logic
41. **Implement** `_check_handoff()` method
42. **Implement** `get_stats()` method

### Phase 6: Module Exports (15 min)

43. **Update** `src/mycoder/router/__init__.py` with all exports
44. **Add** imports to `src/mycoder/__init__.py` (if applicable)

### Phase 7: Unit Tests (60 min)

45. **Create** `tests/unit/test_intent_classifier.py`
46. **Write** tests for pattern matching (COMPLEX, SIMPLE, REVIEW)
47. **Write** tests for token estimation
48. **Write** tests for complexity determination
49. **Create** `tests/unit/test_task_context.py`
50. **Write** tests for TaskContext methods
51. **Create** `tests/unit/test_model_router.py`
52. **Write** tests for `_select_adapter()` with different budgets
53. **Write** tests for `_check_handoff()` logic
54. **Write** tests for FailureMemory constraint injection

### Phase 8: Integration Tests (45 min)

55. **Create** `tests/integration/test_model_router_integration.py`
56. **Write** test: full orchestration flow (mock adapters)
57. **Write** test: budget constraints respected
58. **Write** test: FailureMemory warnings injected
59. **Run** all tests: `poetry run pytest tests/unit/test_*router* tests/unit/test_*classifier* -v`

### Phase 9: Final Verification (15 min)

60. **Run** formatter: `poetry run black src/mycoder/router/ && poetry run isort src/mycoder/router/`
61. **Run** type checker: `poetry run mypy src/mycoder/router/`
62. **Run** full test suite: `poetry run pytest tests/unit/ -v`
63. **Update** `AGENTS.md` with implementation notes

---

## Pseudo-code: route_request() Flow

```python
async def route_request(self, prompt, budget, context, ...):
    # 1. CLASSIFY
    classification = self.classifier.classify(prompt)
    #    → TaskComplexity.COMPLEX, confidence=0.85

    # 2. SELECT ROLE
    role = COMPLEXITY_ROLE_MAP[classification.complexity]
    #    → ModelRole.ARCHITECT

    # 3. GET FAILURES
    advisory = self.failure_memory.check_advisory(
        tool_name="code_pattern",
        params={"pattern": extract_pattern(prompt)}
    )
    if advisory.result == BLOCK:
        context.failure_warnings.append(advisory.reason)

    # 4. BUILD SYSTEM PROMPT
    system_prompt = f"""
    You are the ARCHITECT...

    ## CONSTRAINTS (from previous failures)
    - Do not use subprocess.run (failed on Android)
    - Avoid global state (caused race conditions)
    """

    # 5. SELECT ADAPTER
    model_info = BUDGET_MODEL_MAP[budget][role]
    #    → CLAUDE_OPUS_4 (for ARCHITECT + UNLIMITED budget)
    adapter = self.adapters[model_info.name]

    # 6. EXECUTE
    response = await adapter.query(
        prompt=prompt,
        system_prompt=system_prompt,
        stream_callback=stream_callback,
    )

    # 7. CHECK HANDOFF
    if role == ARCHITECT and "implement" in response.content:
        return RouterResult(
            ...,
            requires_handoff=True,
            next_role=ModelRole.WORKER,
            handoff_prompt=f"Plan:\n{response.content}\n\nImplement this."
        )

    return RouterResult(success=True, content=response.content, ...)
```

---

## Test File Template

```python
"""Unit tests for ModelRouter and IntentClassifier."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from mycoder.router.intent_classifier import IntentClassifier, ClassificationResult
from mycoder.router.task_context import (
    BudgetTier,
    ModelRole,
    TaskComplexity,
    TaskContext,
)
from mycoder.router.model_router import ModelRouter


class TestIntentClassifier:
    """Tests for intent classification."""

    @pytest.fixture
    def classifier(self):
        return IntentClassifier()

    def test_complex_refactoring_detected(self, classifier):
        result = classifier.classify("Refactor the authentication module")
        assert result.complexity == TaskComplexity.COMPLEX
        assert any("Refactoring" in r for r in result.reasons)

    def test_simple_typo_fix(self, classifier):
        result = classifier.classify("Fix the typo in README")
        assert result.complexity == TaskComplexity.TRIVIAL

    def test_review_pattern(self, classifier):
        result = classifier.classify("Review all changes for regressions")
        assert result.complexity == TaskComplexity.REVIEW

    def test_large_context_triggers_review(self, classifier):
        # Simulate large file context
        files = [f"file_{i}.py" for i in range(200)]
        result = classifier.classify("Check this code", file_context=files)
        assert result.complexity == TaskComplexity.REVIEW


class TestTaskContext:
    """Tests for TaskContext."""

    def test_add_execution_tracks_cost(self):
        ctx = TaskContext(original_prompt="test", budget_remaining_usd=10.0)

        ctx.add_execution(
            role=ModelRole.WORKER,
            model_name="gpt-4o",
            prompt="test prompt",
            response="test response",
            cost_usd=0.05,
            duration_ms=500,
        )

        assert ctx.cost_so_far_usd == 0.05
        assert ctx.budget_remaining_usd == 9.95
        assert len(ctx.execution_history) == 1


class TestModelRouter:
    """Tests for ModelRouter."""

    @pytest.fixture
    def router(self):
        return ModelRouter(default_budget=BudgetTier.STANDARD)

    def test_complexity_role_mapping(self, router):
        assert router.COMPLEXITY_ROLE_MAP[TaskComplexity.COMPLEX] == ModelRole.ARCHITECT
        assert router.COMPLEXITY_ROLE_MAP[TaskComplexity.SIMPLE] == ModelRole.WORKER
        assert router.COMPLEXITY_ROLE_MAP[TaskComplexity.REVIEW] == ModelRole.REVIEWER

    @pytest.mark.asyncio
    async def test_budget_constraint_selects_cheaper_model(self, router):
        # Mock adapter
        mock_adapter = AsyncMock()
        mock_adapter.model_info = MagicMock(name="gpt-4o-mini")
        router.adapters["gpt-4o-mini"] = mock_adapter

        # With MINIMAL budget, should select cheaper model
        adapter = router._select_adapter(
            role=ModelRole.WORKER,
            budget=BudgetTier.MINIMAL,
            context=TaskContext(original_prompt="test"),
        )

        # Verify cheaper model selected
        # (actual assertion depends on BUDGET_MODEL_MAP configuration)
```

---

## Acceptance Criteria

1. **Intent Classification** correctly identifies TRIVIAL/SIMPLE/MEDIUM/COMPLEX/REVIEW
2. **Budget tiers** respected - MINIMAL uses Haiku/Flash, UNLIMITED uses Opus
3. **FailureMemory warnings** injected into system prompts
4. **Handoffs** work correctly: Architect → Worker → Reviewer
5. **Cost tracking** accurate across all executions
6. **Adapters** properly abstracted - easy to add new providers
7. **All tests pass**: `poetry run pytest tests/unit/test_*router* -v`

---

## Notes for Codex

- Use `from __future__ import annotations` for forward references
- Model adapters should handle API errors gracefully (return AdapterResponse with error)
- Keep adapters thin - they just translate between our interface and provider APIs
- Use existing `api_providers.py` patterns for API calls
- Test with mocked adapters first, then add integration tests with real APIs
- Follow existing code style in `src/mycoder/` (see `api_providers.py`, `tool_registry.py`)
