from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from ..task_context import ModelRole, TaskContext


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
    tokens_per_second: int  # Output speed

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
        **kwargs: Any,
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
        scores = {
            ModelRole.ARCHITECT: self.model_info.architect_score,
            ModelRole.WORKER: self.model_info.worker_score,
            ModelRole.REVIEWER: self.model_info.reviewer_score,
        }
        return scores.get(role, 0.0)
