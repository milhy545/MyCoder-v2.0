"""Unit tests for self-evolve risk assessor."""

from mycoder.self_evolve.risk_assessor import RiskAssessor


def test_risk_assessor_scores_source_changes() -> None:
    assessor = RiskAssessor()
    diff = """
    diff --git a/src/mycoder/example.py b/src/mycoder/example.py
    --- a/src/mycoder/example.py
    +++ b/src/mycoder/example.py
    +print("hello")
    """.strip()
    assessment = assessor.assess(diff)
    assert assessment.score > 0.1
    assert any("source" in note.lower() for note in assessment.notes)


def test_risk_assessor_highlights_large_diff() -> None:
    assessor = RiskAssessor()
    diff_lines = "\n".join(["+line" for _ in range(600)])
    diff = (
        "diff --git a/src/mycoder/example.py b/src/mycoder/example.py\n"
        "--- a/src/mycoder/example.py\n"
        "+++ b/src/mycoder/example.py\n"
        f"{diff_lines}"
    )
    assessment = assessor.assess(diff)
    assert assessment.score >= 0.3
    assert any("large diff" in note.lower() for note in assessment.notes)
