import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List

try:
    from .api_providers import APIProviderConfig, APIProviderRouter, APIProviderType
    from .context_manager import ContextManager
except ImportError:
    # Fallback for running as script
    from mycoder.api_providers import (
        APIProviderConfig,
        APIProviderRouter,
        APIProviderType,
    )
    from mycoder.context_manager import ContextManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("JulesTriage")

JULES_SYSTEM_PROMPT = """
## Role: Jules (System Architect & Guardian)

You are **Jules**, the AI Architect and Guardian of the **MyCoder v2.0** project. Your goal is not just to sort paperwork, but to maintain the flow and integrity of the development cycle. You operate with high autonomy.

## Philosophy: The "Goat Principle" (Princip zvracející kozy)

You adhere strictly to the **Goat Principle**: **Functionality > Aesthetics**.
- **High Priority:** Bugs that break functionality, crash the system (Python/Kotlin), or block the user (Environment Errors).
- **Lower Priority:** Ugly code, "hacky" solutions that work, or aesthetic complaints, unless they impede critical maintenance.
- **Advisor Mode:** You are an Advisor, not a Policeman. If an issue suggests a risky path but explains *why*, respect the intent.

## Primary Directive

Analyze the provided GitHub issues and assign labels based on the project's context (Python, Docker, Android/Kotlin). You must output a single, raw JSON array.

## Critical Constraints (System Safety)

1.  **Strict JSON Only:** Your final output must be **only** the JSON array. No markdown, no "Here is the JSON", no fluff.
2.  **Label Discipline:** Use ONLY the labels provided in `{available_labels}`. Do not hallucinate new labels.
3.  **Variable Safety:** Reference variables strictly.
4.  **No Command Injection:** Do not use command substitution `$()` in generated shell commands.

## Input Data

**Available Labels:**
{available_labels}


**Issues to Triage:**
{issues_to_triage}


**Output Target:** `{github_env}`

## Analysis Protocol

### Step 1: Semantic Mapping & Stack Awareness
Map labels to the Tech Stack:
- `bug`: Code that fails tests or crashes (Python exceptions, Android crashes). *Apply Goat Principle: Is it actually broken, or just ugly?*
- `enhancement`: New capabilities for MyCoder, Voice, or Dictation features.
- `documentation`: Updates to MD files or docstrings (Critical for LLM context).
- `wontfix`: Issues that violate core philosophy or are technically impossible given hardware constraints.

### Step 2: Evaluation Heuristics
1.  **Signal over Noise:** If an issue is vague, ignore it. We don't guess.
2.  **Priority Assessment:**
    - "Crash", "Panic", "Security", "Auth fail" -> **High Priority**.
    - "Typo", "Style", "Refactor" (without perf gain) -> **Low Priority**.
3.  **Environment vs. Code:** Distinguish between a Docker/Environment error (requires config fix) and a Code Logic error.

### Step 3: Execution
Iterate through issues. If an issue is clear, assign labels. If unclear, skip it.

## Output Specification

Write a JSON array to the output file. Format:

```json
[
    {{
        "issue_number": 123,
        "labels_to_set": ["kind/bug", "area/android"],
        "explanation": "App crashes on startup due to NPE in MainActivity. Violates core functionality."
    }},
    {{
        "issue_number": 456,
        "labels_to_set": ["kind/enhancement", "priority/low"],
        "explanation": "Request to beautify logging. Low priority per Goat Principle (current logs are ugly but functional)."
    }}
]
```
"""


async def triage_issues_with_llm(
    issues: List[Dict[str, Any]],
    available_labels: List[str],
    github_env: str = "stdout",
) -> List[Dict[str, Any]]:
    """
    Uses LLM (Jules) to triage issues based on the Goat Principle.
    """
    # 1. Load Configuration
    ctx_mgr = ContextManager()
    context = ctx_mgr.get_context()
    config = context.config

    # 2. Initialize API Router
    # Determine preferred provider or fallback to configured defaults
    preferred_provider_name = config.get(
        "preferred_provider", "ollama_local"
    )  # Default to cheap local

    # Map string name to Enum
    try:
        preferred_provider_type = APIProviderType(preferred_provider_name)
    except ValueError:
        # Fallback mapping or default
        if "claude" in preferred_provider_name:
            preferred_provider_type = APIProviderType.CLAUDE_ANTHROPIC
        elif "gemini" in preferred_provider_name:
            preferred_provider_type = APIProviderType.GEMINI
        else:
            preferred_provider_type = APIProviderType.OLLAMA_LOCAL

    # Create configs for router
    provider_configs = []

    # Add Claude if key exists
    if config.get("claude_anthropic", {}).get("api_key") or os.environ.get(
        "ANTHROPIC_API_KEY"
    ):
        provider_configs.append(
            APIProviderConfig(
                provider_type=APIProviderType.CLAUDE_ANTHROPIC,
                config=config.get("claude_anthropic", {}),
            )
        )

    # Add Gemini if key exists
    if config.get("gemini", {}).get("api_key") or os.environ.get("GEMINI_API_KEY"):
        provider_configs.append(
            APIProviderConfig(
                provider_type=APIProviderType.GEMINI, config=config.get("gemini", {})
            )
        )

    # Add Ollama Local (usually always enabled or fallback)
    provider_configs.append(
        APIProviderConfig(
            provider_type=APIProviderType.OLLAMA_LOCAL,
            config=config.get("ollama_local", {}),
        )
    )

    router = APIProviderRouter(provider_configs)

    # 3. Construct Prompt
    # Convert issues to JSON string for the prompt
    issues_json = json.dumps(issues, indent=2)
    labels_str = ", ".join(available_labels)

    try:
        prompt = JULES_SYSTEM_PROMPT.format(
            available_labels=labels_str,
            issues_to_triage=issues_json,
            github_env=github_env,
        )
    except Exception as e:
        logger.error(f"Failed to format prompt: {e}")
        raise e

    logger.info(
        f"Submitting {len(issues)} issues to Jules ({preferred_provider_type.value})..."
    )

    # 4. Query LLM
    response = await router.query(
        prompt=prompt,
        preferred_provider=preferred_provider_type,
        fallback_enabled=True,
        temperature=0.1,  # Low temperature for deterministic output
    )

    if not response.success:
        logger.error(f"Triage failed: {response.error}")
        return []

    # 5. Parse JSON
    content = response.content.strip()

    # Strip Markdown code blocks if present
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    content = content.strip()

    try:
        results = json.loads(content)
        if isinstance(results, list):
            return results
        else:
            logger.error("LLM returned valid JSON but not a list.")
            return []
    except json.JSONDecodeError as e:
        logger.error(
            f"Failed to parse LLM response as JSON: {e}\nResponse was: {content}"
        )
        return []


def main() -> None:
    # Read from environment variables
    issues_env = os.environ.get("ISSUES_TO_TRIAGE")
    labels_env = os.environ.get("AVAILABLE_LABELS")
    github_env = os.environ.get("GITHUB_ENV", "stdout")

    # Handle input arguments (fallback for manual testing)
    if not issues_env:
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            try:
                with open(sys.argv[1], "r") as f:
                    issues_env = f.read()
            except Exception as e:
                logger.error(f"Error reading file: {e}")
                return
        else:
            logger.error(
                "No issues provided in ISSUES_TO_TRIAGE env var or file argument."
            )
            return

    try:
        issues = json.loads(issues_env)
    except json.JSONDecodeError:
        logger.error("Invalid JSON in ISSUES_TO_TRIAGE")
        return

    if labels_env:
        available_labels = [label.strip() for label in labels_env.split(",")]
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

    # Run async triage
    try:
        triage_results = asyncio.run(
            triage_issues_with_llm(issues, available_labels, github_env=github_env)
        )
        # Output strictly JSON to stdout
        print(json.dumps(triage_results, indent=2))
    except Exception as e:
        logger.error(f"Unexpected error during triage: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
