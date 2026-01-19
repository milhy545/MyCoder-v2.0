#!/usr/bin/env python3
"""
Headless Runner for MyCoder CI/CD Integration.

Designed for automated environments (GitHub Actions, Jenkins).
Output: JSONL (structured logging)
Input: stdin or args
"""

import sys
import json
import asyncio
import logging
import argparse
from pathlib import Path

# Ensure src is in path
sys.path.append(str(Path(__file__).parent.parent))

from mycoder.enhanced_mycoder_v2 import EnhancedMyCoderV2
from mycoder.context_manager import ContextManager

class JsonlHandler(logging.Handler):
    """Logs events as JSONL lines for machine parsing."""
    def emit(self, record):
        try:
            log_entry = {
                "timestamp": record.created,
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage()
            }
            # Avoid using logging to print to stdout to prevent recursion if configured wrong,
            # but here we just print to stdout (or stderr).
            # CI logs usually go to stdout/stderr.
            print(json.dumps(log_entry), file=sys.stdout)
        except Exception:
            self.handleError(record)

async def main():
    parser = argparse.ArgumentParser(description="MyCoder Headless Runner")
    parser.add_argument("prompt", nargs="?", help="Task description")
    parser.add_argument("--auto-approve", "-y", action="store_true", help="Execute tools without confirmation")
    parser.add_argument("--working-dir", "-w", default=".", help="Working directory")

    args = parser.parse_args()

    # Configure Logging
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Remove default handlers
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    root_logger.addHandler(JsonlHandler())

    # Determine Prompt
    prompt = args.prompt
    if not prompt:
        # Check stdin
        if not sys.stdin.isatty():
            prompt = sys.stdin.read().strip()

    if not prompt:
        logging.error("No prompt provided via argument or stdin")
        sys.exit(1)

    logging.info(f"Initializing Headless Agent. Auto-approve: {args.auto_approve}")

    try:
        working_dir = Path(args.working_dir).resolve()

        # Load Context
        ctx_mgr = ContextManager(working_dir)
        context_data = ctx_mgr.get_context()

        # Initialize Agent
        coder = EnhancedMyCoderV2(
            working_directory=working_dir,
            config=context_data.config
        )

        await coder.initialize()

        # For security in headless, we force use_tools based on flag
        # If auto_approve is False, we DISABLE tools to prevent hanging/unauthorized actions.
        use_tools = args.auto_approve

        logging.info("Processing request...")
        response = await coder.process_request(
            prompt,
            use_tools=use_tools,
            continue_session=False
        )

        # Output result
        # We print a specific RESULT JSON at the end for the caller to parse
        result_payload = {
            "success": response.get("success", False),
            "content": response.get("content", ""),
            "metadata": response.get("metadata", {}),
            "error": response.get("error")
        }

        # Use a distinct prefix or file for output if mixed with logs?
        # Standard: Last line is result? Or just log it.
        # Required: "výstup čistý JSONL (pro logy)"
        logging.info(f"Task complete. Success: {result_payload['success']}")

        # If caller needs the response content, they can parse the last log message or we can print it specifically.
        # But for CI/CD, usually exit code is key.

        if response.get("success"):
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        logging.exception("Fatal error in headless runner")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
