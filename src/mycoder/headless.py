#!/usr/bin/env python3
"""
Headless Runner for MyCoder CI/CD Integration.

Designed for automated environments (GitHub Actions, Jenkins).
Output: JSONL (structured logging)
Input: stdin or args
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional, TextIO

# Ensure src is in path
sys.path.append(str(Path(__file__).parent.parent))

from mycoder.context_manager import ContextManager
from mycoder.enhanced_mycoder_v2 import EnhancedMyCoderV2


class JsonlHandler(logging.Handler):
    """Logs events as JSONL lines for machine parsing."""

    def __init__(self, stream: Optional[TextIO] = None) -> None:
        super().__init__()
        self.stream = stream or sys.stderr

    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_entry = {
                "timestamp": record.created,
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            # Log to the specified stream (usually stderr or a file)
            # to keep stdout clean for the final result.
            print(json.dumps(log_entry), file=self.stream)
            self.stream.flush()
        except Exception:
            self.handleError(record)


async def main() -> None:
    parser = argparse.ArgumentParser(description="MyCoder Headless Runner")
    parser.add_argument("prompt", nargs="?", help="Task description")
    parser.add_argument(
        "--auto-approve",
        "-y",
        action="store_true",
        help="Execute tools without confirmation",
    )
    parser.add_argument("--working-dir", "-w", default=".", help="Working directory")
    parser.add_argument("--output", "-o", help="Output result JSON to a file")
    parser.add_argument("--log-file", help="Log JSONL to a specific file")

    args = parser.parse_args()

    # Configure Logging
    log_stream = sys.stderr
    log_file_handle = None

    if args.log_file:
        try:
            log_path = Path(args.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_file_handle = log_path.open("a", encoding="utf-8")
            log_stream = log_file_handle
        except Exception as e:
            print(f"Error opening log file: {e}", file=sys.stderr)
            sys.exit(1)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Remove default handlers
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
    root_logger.addHandler(JsonlHandler(stream=log_stream))

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
            working_directory=working_dir, config=context_data.config
        )

        await coder.initialize()

        # For security in headless, we force use_tools based on flag
        # If auto_approve is False, we DISABLE tools to prevent hanging/unauthorized actions.
        use_tools = args.auto_approve

        logging.info("Processing request...")
        response = await coder.process_request(
            prompt, use_tools=use_tools, continue_session=False
        )

        # Output result
        # We print a specific RESULT JSON at the end for the caller to parse
        result_payload = {
            "success": response.get("success", False),
            "content": response.get("content", ""),
            "metadata": response.get("metadata", {}),
            "error": response.get("error"),
        }

        result_json = json.dumps(result_payload)
        if args.output:
            try:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(result_json, encoding="utf-8")
                logging.info(f"Result written to {args.output}")
            except Exception as e:
                logging.error(f"Failed to write result to {args.output}: {e}")
                # Fallback to stdout if file write fails
                print(result_json)
        else:
            # Print to stdout for caller to capture
            print(result_json)

        logging.info(f"Task complete. Success: {result_payload['success']}")

        if response.get("success"):
            sys.exit(0)
        else:
            sys.exit(1)

    except Exception as e:
        logging.exception("Fatal error in headless runner")
        sys.exit(1)
    finally:
        if log_file_handle:
            log_file_handle.close()


if __name__ == "__main__":
    asyncio.run(main())
