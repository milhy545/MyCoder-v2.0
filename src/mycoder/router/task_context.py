from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class ModelRole(Enum):
    """The three model roles in the Triad system."""

    ARCHITECT = "architect"  # Claude Opus - complex planning
    WORKER = "worker"  # GPT-4o/Codex - code generation
    REVIEWER = "reviewer"  # Gemini 1.5 Pro - context review


class TaskComplexity(Enum):
    """Classified complexity of a task."""

    TRIVIAL = "trivial"  # One-liner fix, typo correction
    SIMPLE = "simple"  # Small function, single file change
    MEDIUM = "medium"  # Multiple files, some coordination
    COMPLEX = "complex"  # Architecture, refactoring, hard debug
    REVIEW = "review"  # Needs large context analysis


class BudgetTier(Enum):
    """Budget constraint tiers."""

    MINIMAL = "minimal"  # Only free/cheapest models (Haiku, local)
    LOW = "low"  # Prefer cheap (Sonnet, Flash)
    STANDARD = "standard"  # Balanced (Sonnet, GPT-4o)
    HIGH = "high"  # Allow expensive (Opus occasionally)
    UNLIMITED = "unlimited"  # Full access to Opus


class HandoffType(Enum):
    """Types of model handoffs."""

    PLAN_TO_CODE = "plan_to_code"  # Architect → Worker
    CODE_TO_REVIEW = "code_to_review"  # Worker → Reviewer
    REVIEW_TO_FIX = "review_to_fix"  # Reviewer → Worker
    ESCALATE = "escalate"  # Worker → Architect (stuck)


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
        self.execution_history.append(
            {
                "role": role.value,
                "model": model_name,
                "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                "response_preview": (
                    response[:500] + "..." if len(response) > 500 else response
                ),
                "cost_usd": cost_usd,
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat(),
            }
        )
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
