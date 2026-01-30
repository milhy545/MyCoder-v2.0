"""
Intent classification for determining task complexity and model routing.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

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
        (
            r"\b(debug|investigate|diagnose|why)\b.*\b(crash|fail|error|bug)\b",
            "Complex debugging",
        ),
        (
            r"\b(implement|create|build)\b.*\b(feature|system|module)\b",
            "Feature implementation",
        ),
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

    def classify(
        self, prompt: str, file_context: Optional[List[str]] = None
    ) -> ClassificationResult:
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

    def _estimate_tokens(
        self, prompt: str, file_context: Optional[List[str]] = None
    ) -> int:
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

        # Review takes precedence
        if review_score >= 2:
            return TaskComplexity.REVIEW, 0.9
        if review_score == 1 and complex_score == 0:
            return TaskComplexity.REVIEW, 0.7

        # Complex takes precedence over simple
        if complex_score >= 2:
            return TaskComplexity.COMPLEX, 0.85
        if complex_score == 1 and simple_score == 0:
            return TaskComplexity.COMPLEX, 0.7

        # Simple
        if simple_score >= 2:
            return TaskComplexity.TRIVIAL, 0.9
        if simple_score == 1 and complex_score == 0:
            # Single simple match (like typo) is TRIVIAL
            return TaskComplexity.TRIVIAL, 0.8

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

        return []
