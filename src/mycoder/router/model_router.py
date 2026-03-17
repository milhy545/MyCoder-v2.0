"""
Model Router & Orchestrator for MyCoder v2.2.0

Implements the Triad strategy:
- Architect (Opus): Complex planning
- Worker (GPT-4o/Sonnet): Code generation
- Reviewer (Gemini): Large context review
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from ..self_evolve.failure_memory import AdvisoryResult, FailureMemory
from ..tool_registry import ToolRegistry
from .adapters import BUDGET_MODEL_MAP
from .adapters.base import AdapterResponse, BaseModelAdapter
from .intent_classifier import ClassificationResult, IntentClassifier
from .task_context import (
    BudgetTier,
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
        # We iterate through UNLIMITED tier to get all possible models
        for model_info in BUDGET_MODEL_MAP[BudgetTier.UNLIMITED].values():
            if model_info.name in self.adapters:
                continue

            adapter: Optional[BaseModelAdapter] = None
            if model_info.provider == "anthropic":
                adapter = ClaudeAdapter(model_info)
            elif model_info.provider == "openai":
                adapter = OpenAIAdapter(model_info)
            elif model_info.provider == "google":
                adapter = GeminiAdapter(model_info)
            else:
                continue

            if adapter and await adapter.initialize():
                self.adapters[model_info.name] = adapter
                logger.info(f"Initialized adapter: {model_info.name}")

        # Also initialize other tiers' unique models if any
        for tier in BudgetTier:
            if tier == BudgetTier.UNLIMITED:
                continue
            for model_info in BUDGET_MODEL_MAP.get(tier, {}).values():
                if model_info.name in self.adapters:
                    continue

                adapter = None
                if model_info.provider == "anthropic":
                    adapter = ClaudeAdapter(model_info)
                elif model_info.provider == "openai":
                    adapter = OpenAIAdapter(model_info)
                elif model_info.provider == "google":
                    adapter = GeminiAdapter(model_info)

                if adapter and await adapter.initialize():
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

        return await self._orchestrate_loop(
            prompt,
            budget or self.default_budget,
            max_handoffs,
            stream_callback,
            context,
        )

    async def _orchestrate_loop(
        self,
        prompt: str,
        budget: BudgetTier,
        max_handoffs: int,
        stream_callback: Optional[Callable[[str], None]],
        context: TaskContext,
    ) -> RouterResult:
        current_prompt = prompt
        handoff_count = 0
        force_role: Optional[ModelRole] = None
        result: Optional[RouterResult] = None

        while handoff_count <= max_handoffs:
            result = await self.route_request(
                prompt=current_prompt,
                budget=budget,
                context=context,
                stream_callback=stream_callback,
                force_role=force_role,
            )

            if not result.success or not result.requires_handoff:
                return result

            force_role = result.next_role
            current_prompt = result.handoff_prompt or result.content
            handoff_count += 1

        logger.warning(f"Max handoffs ({max_handoffs}) reached")
        if result is None:
            # Should not happen if max_handoffs >= 0
            return RouterResult(
                success=False,
                content="Loop did not execute",
                model_role=ModelRole.WORKER,
                model_name="none",
                cost_usd=0.0,
                duration_ms=0,
                tokens_used=0,
                task_context=context,
                error="Internal loop error",
            )
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
        # Simple hash for demo purposes; in prod use semantic analysis or tool name
        advisory = self.failure_memory.check_advisory(
            tool_name="model_router",
            params={"prompt_hash": str(hash(prompt) % 10000)},
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
            # Logic: If I asked for High/Standard but that model isn't init (e.g. no key),
            # fall back to Low/Minimal if available.
            # But wait, usually fallback goes DOWN in cost (standard -> low).
            # If standard is missing, maybe I want low.
            for fallback_budget in [
                BudgetTier.STANDARD,
                BudgetTier.LOW,
                BudgetTier.MINIMAL,
            ]:
                if fallback_budget == budget:
                    continue

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
        classification: ClassificationResult,
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
            if (
                "implement" in response.content.lower()
                or "step" in response.content.lower()
            ):
                handoff_prompt = (
                    f"## Task\n{context.original_prompt}\n\n"
                    f"## Implementation Plan\n{response.content}\n\n"
                    "Implement the plan above. Generate complete, working code."
                )
                return True, ModelRole.WORKER, handoff_prompt

        # Worker → Reviewer handoff (for complex tasks)
        if current_role == ModelRole.WORKER:
            if classification.complexity in [
                TaskComplexity.COMPLEX,
                TaskComplexity.MEDIUM,
            ]:
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
            context.review_passed = (
                "approved" in response.content.lower()
                or "lgtm" in response.content.lower()
            )

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
                role.value: count for role, count in self.requests_by_role.items()
            },
            "adapters_available": list(self.adapters.keys()),
        }
