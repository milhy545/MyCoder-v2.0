import json
import os
import sys
from typing import List, Dict, Any


def triage_issues(
    issues: List[Dict[str, Any]], available_labels: List[str]
) -> List[Dict[str, Any]]:
    results = []

    # Keyword mappings for labels
    bug_keywords = [
        "crash",
        "error",
        "fail",
        "broken",
        "exception",
        "traceback",
        "panic",
        "npe",
    ]
    enhancement_keywords = [
        "feature",
        "add",
        "request",
        "implement",
        "new capability",
        "support",
    ]
    docs_keywords = ["doc", "readme", "typo", "clarify", "guide", "documentation"]

    # Priority keywords
    high_priority_keywords = [
        "critical",
        "security",
        "auth",
        "panic",
        "crash",
        "blocker",
    ]
    low_priority_keywords = ["style", "formatting", "color", "beautify", "hacky"]

    # Area keywords
    android_keywords = [
        "android",
        "apk",
        "mobile",
        "phone",
        "kotlin",
        "viewbinding",
        "activity",
        "fragment",
        "gradle",
        "intent",
    ]
    docker_keywords = ["docker", "container", "image", "compose", "k8s", "kubernetes"]

    for issue in issues:
        title = issue.get("title", "").lower()
        body = issue.get("body", "").lower()
        full_text = f"{title} {body}"

        labels_to_set = set()
        explanation_parts = []

        # Check specific constraints/wontfix
        if "impossible" in full_text or "hardware constraint" in full_text:
            labels_to_set.add("wontfix")
            explanation_parts.append("Violates hardware constraints or impossible.")

        # Map kind
        if any(kw in full_text for kw in bug_keywords):
            labels_to_set.add("kind/bug")
            explanation_parts.append("Detected crash or failure pattern.")
        elif any(kw in full_text for kw in enhancement_keywords):
            labels_to_set.add("kind/enhancement")
            explanation_parts.append("Request for new capability.")
        elif any(kw in full_text for kw in docs_keywords):
            labels_to_set.add("documentation")
            explanation_parts.append("Documentation update.")

        # Map priority
        if any(kw in full_text for kw in high_priority_keywords):
            labels_to_set.add("priority/high")
            explanation_parts.append("High priority signal detected (security/crash).")
        elif any(kw in full_text for kw in low_priority_keywords):
            labels_to_set.add("priority/low")
            explanation_parts.append("Low priority signal (aesthetic/style).")

        # Map area
        if any(kw in full_text for kw in android_keywords):
            labels_to_set.add("area/android")
        if any(kw in full_text for kw in docker_keywords):
            labels_to_set.add("area/docker")

        # Filter against available labels
        final_labels = [label for label in labels_to_set if label in available_labels]

        # Goat Principle: Ignore noise
        if not final_labels:
            continue

        # Goat Principle: Functionality > Aesthetics
        if "kind/bug" in final_labels and "priority/low" in final_labels:
            # Re-evaluate: if it breaks functionality, it's not low priority unless it's just ugly
            if "crash" in full_text or "panic" in full_text:
                final_labels.remove("priority/low")
                if "priority/high" in available_labels:
                    final_labels.append("priority/high")
                    explanation_parts.append("Elevated to high priority due to crash.")

        results.append(
            {
                "issue_number": issue.get("number"),
                "labels_to_set": sorted(list(set(final_labels))),
                "explanation": " ".join(explanation_parts),
            }
        )

    return results


def main():
    # Read from environment variables
    issues_env = os.environ.get("ISSUES_TO_TRIAGE")
    labels_env = os.environ.get("AVAILABLE_LABELS")

    if not issues_env:
        # Fallback for testing/manual run if file path provided
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            try:
                with open(sys.argv[1], "r") as f:
                    issues_env = f.read()
            except Exception as e:
                print(f"Error reading file: {e}", file=sys.stderr)
                return
        else:
            print(
                "No issues provided in ISSUES_TO_TRIAGE env var or file argument.",
                file=sys.stderr,
            )
            return

    try:
        issues = json.loads(issues_env)
    except json.JSONDecodeError:
        print("Invalid JSON in ISSUES_TO_TRIAGE", file=sys.stderr)
        return

    if labels_env:
        available_labels = labels_env.split(",")
        # Clean up whitespace
        available_labels = [label.strip() for label in available_labels]
    else:
        # Default fallback set if not provided
        available_labels = [
            "kind/bug",
            "kind/enhancement",
            "documentation",
            "wontfix",
            "priority/high",
            "priority/low",
            "area/android",
            "area/docker",
        ]

    triage_results = triage_issues(issues, available_labels)

    # Output strictly JSON
    print(json.dumps(triage_results, indent=2))


if __name__ == "__main__":
    main()
