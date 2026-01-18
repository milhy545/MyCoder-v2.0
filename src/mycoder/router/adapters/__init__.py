from ..task_context import BudgetTier, ModelRole
from .base import AdapterResponse, BaseModelAdapter, ModelCapability, ModelInfo

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
