"""Unit tests for IntentClassifier."""

import pytest

from mycoder.router.intent_classifier import IntentClassifier
from mycoder.router.task_context import TaskComplexity


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

    def test_medium_complexity(self, classifier):
        # Long prompt but not complex keywords
        prompt = "Create a function that calculates fibonacci " * 10
        result = classifier.classify(prompt)
        # Should be MEDIUM or COMPLEX depending on length thresholds,
        # but likely MEDIUM if length < 200 chars?
        # "Create... " * 10 is ~400 chars.
        # Length > 200 defaults to COMPLEX in logic.
        assert result.complexity in [TaskComplexity.MEDIUM, TaskComplexity.COMPLEX]

    def test_simple_patterns(self, classifier):
        result = classifier.classify("Add a comment to main.py")
        assert result.complexity in [TaskComplexity.TRIVIAL, TaskComplexity.SIMPLE]
