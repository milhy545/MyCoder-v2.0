"""Direct Claude CLI interface with subprocess management.

This module provides a direct interface to Claude CLI through subprocess calls,
handling streaming output, command building, error recovery, and process management.
It's designed as a fallback when SDK integration fails or is unavailable.
"""

import asyncio
import json
import logging
import os
import subprocess
import time
import uuid
from asyncio.subprocess import Process
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Union

from .auth_manager import AuthManager
from .exceptions import ClaudeCLIError, ClaudeParsingError, ClaudeTimeoutError
from .models import AuthConfig, ClaudeResponse, StreamType, StreamUpdate

logger = logging.getLogger(__name__)


@dataclass
class CLIResponse:
    """Response from Claude CLI execution.
    
    Contains all response data from Claude CLI subprocess execution,
    including parsed content, metadata, and execution statistics.
    """
    
    content: str
    session_id: str
    cost: float = 0.0
    duration_ms: int = 0
    num_turns: int = 0
    is_error: bool = False
    error_type: Optional[str] = None
    tools_used: List[Dict[str, Any]] = field(default_factory=list)
    raw_messages: List[Dict[str, Any]] = field(default_factory=list)
    exit_code: int = 0
    stderr: str = ""
    
    def to_claude_response(self) -> ClaudeResponse:
        """Convert to standard ClaudeResponse format."""
        return ClaudeResponse(
            content=self.content,
            session_id=self.session_id,
            cost=self.cost,
            duration_ms=self.duration_ms,
            num_turns=self.num_turns,
            is_error=self.is_error,
            error_type=self.error_type,
            tools_used=self.tools_used,
            created_at=time.time(),
        )


class CLIInterface:
    """Direct interface to Claude CLI via subprocess.
    
    Provides comprehensive Claude CLI integration including:
    - Command building and execution
    - Streaming output parsing
    - Session management
    - Error handling and recovery
    - Memory-optimized processing
    
    Example:
        ```python
        cli = CLIInterface()
        
        # Simple query
        response = await cli.execute(
            prompt="Hello Claude",
            working_directory=Path(".")
        )
        
        # With streaming
        async def on_stream(update):
            print(f"[{update.type}] {update.content}")
        
        response = await cli.execute(
            prompt="Create a function",
            working_directory=Path("."),
            stream_callback=on_stream
        )
        ```
    """
    
    def __init__(
        self,
        config: Optional[AuthConfig] = None,
        auth_manager: Optional[AuthManager] = None,
    ):
        """Initialize CLI interface.
        
        Args:
            config: Configuration for CLI operations
            auth_manager: Authentication manager instance
            
        Raises:
            ClaudeCLIError: If initialization fails
        """
        self.config = config or AuthConfig()
        self.auth_manager = auth_manager or AuthManager(self.config)
        
        # Process tracking
        self.active_processes: Dict[str, Process] = {}
        
        # Performance settings
        self.max_message_buffer = 1000  # Limit message history for memory
        self.streaming_buffer_size = 65536  # 64KB streaming buffer
        
        # Verify Claude CLI is available and authenticated
        if not self.auth_manager.is_authenticated():
            raise ClaudeCLIError(
                "Claude CLI is not authenticated",
                suggestions=[
                    "Run 'claude auth login' to authenticate",
                    "Verify Claude CLI installation",
                    "Check internet connectivity",
                ]
            )
        
        logger.info(
            "CLI interface initialized",
            config_dir=str(self.config.claude_config_dir),
            timeout=self.config.timeout_seconds,
        )
    
    async def execute(
        self,
        prompt: str,
        working_directory: Optional[Path] = None,
        session_id: Optional[str] = None,
        continue_session: bool = False,
        stream_callback: Optional[Callable[[StreamUpdate], None]] = None,
        timeout: Optional[float] = None,
    ) -> CLIResponse:
        """Execute Claude CLI command with comprehensive error handling.
        
        Args:
            prompt: Prompt to send to Claude
            working_directory: Directory to run command in
            session_id: Session ID for conversation continuity
            continue_session: Whether to continue existing session
            stream_callback: Callback for streaming updates
            timeout: Command timeout in seconds
            
        Returns:
            CLIResponse with execution results
            
        Raises:
            ClaudeCLIError: If CLI execution fails
            ClaudeTimeoutError: If command times out
            ClaudeParsingError: If response parsing fails
        """
        start_time = time.time()
        process_id = str(uuid.uuid4())
        
        # Use provided working directory or default
        work_dir = working_directory or self.config.working_directory
        
        # Build command
        cmd = self._build_command(
            prompt=prompt,
            session_id=session_id,
            continue_session=continue_session,
        )
        
        logger.info(
            "Executing Claude CLI command",
            process_id=process_id,
            working_directory=str(work_dir),
            session_id=session_id,
            continue_session=continue_session,
            prompt_length=len(prompt),
        )
        
        try:
            # Start subprocess
            process = await self._start_process(cmd, work_dir)
            self.active_processes[process_id] = process
            
            # Handle output with timeout
            response = await asyncio.wait_for(
                self._handle_process_output(
                    process=process,
                    stream_callback=stream_callback,
                    process_id=process_id,
                ),
                timeout=timeout or self.config.timeout_seconds,
            )
            
            # Set execution time
            response.duration_ms = int((time.time() - start_time) * 1000)
            
            # Generate session ID if not provided and not in response
            if not response.session_id:
                response.session_id = session_id or f"cli_{int(time.time())}_{process_id[:8]}"
            
            logger.info(
                "Claude CLI command completed",
                process_id=process_id,
                session_id=response.session_id,
                duration_ms=response.duration_ms,
                cost=response.cost,
                is_error=response.is_error,
            )
            
            return response
            
        except asyncio.TimeoutError:
            # Kill process on timeout
            if process_id in self.active_processes:
                process = self.active_processes[process_id]
                try:
                    process.kill()
                    await process.wait()
                except Exception as e:
                    logger.warning("Failed to kill timed out process", error=str(e))
            
            timeout_val = timeout or self.config.timeout_seconds
            logger.error(
                "Claude CLI command timed out",
                process_id=process_id,
                timeout_seconds=timeout_val,
            )
            
            raise ClaudeTimeoutError(
                f"Claude CLI timed out after {timeout_val}s",
                timeout_seconds=timeout_val,
                operation="cli_execute",
                suggestions=[
                    "Increase timeout value",
                    "Try smaller prompts",
                    "Check system performance",
                    "Verify Claude service availability",
                ]
            )
            
        except Exception as e:
            logger.error(
                "Claude CLI command failed",
                process_id=process_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            
            # Convert to appropriate exception type
            if isinstance(e, (ClaudeCLIError, ClaudeTimeoutError, ClaudeParsingError)):
                raise
            else:
                raise ClaudeCLIError(
                    f"CLI execution failed: {str(e)}",
                    suggestions=[
                        "Check Claude CLI installation",
                        "Verify working directory exists",
                        "Check system resources",
                        "Review command parameters",
                    ]
                )
            
        finally:
            # Clean up process tracking
            if process_id in self.active_processes:
                del self.active_processes[process_id]
    
    async def kill_all_processes(self) -> None:
        """Kill all active Claude processes."""
        if not self.active_processes:
            return
            
        logger.info(
            "Killing active Claude processes",
            count=len(self.active_processes)
        )
        
        for process_id, process in list(self.active_processes.items()):
            try:
                if process.returncode is None:  # Process still running
                    process.kill()
                    await process.wait()
                    
                logger.debug("Killed process", process_id=process_id)
                
            except Exception as e:
                logger.warning(
                    "Failed to kill process",
                    process_id=process_id,
                    error=str(e),
                )
            
            finally:
                # Remove from tracking
                self.active_processes.pop(process_id, None)
        
        logger.info("All Claude processes terminated")
    
    def get_active_process_count(self) -> int:
        """Get number of active processes."""
        return len(self.active_processes)
    
    def _build_command(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        continue_session: bool = False,
    ) -> List[str]:
        """Build Claude CLI command with proper arguments.
        
        Args:
            prompt: User prompt
            session_id: Session ID for continuity
            continue_session: Whether continuing existing session
            
        Returns:
            List of command arguments
        """
        # Find Claude CLI path
        claude_path = self.auth_manager._find_claude_cli()
        if not claude_path:
            raise ClaudeCLIError(
                "Claude CLI executable not found",
                suggestions=[
                    "Install Claude CLI: npm install -g @anthropic-ai/claude-code",
                    "Add Claude CLI to PATH",
                    "Set claude_cli_path in configuration",
                ]
            )
        
        cmd = [claude_path]
        
        # Handle session continuation
        if continue_session and session_id:
            if prompt:
                # Continue session with new prompt
                cmd.extend(["--resume", session_id, "-p", prompt])
            else:
                # Continue without new prompt
                cmd.extend(["--resume", session_id, "--continue"])
        elif prompt:
            # New session or standalone prompt
            cmd.extend(["-p", prompt])
        else:
            # This shouldn't happen, but handle gracefully
            raise ClaudeCLIError(
                "No prompt provided and not continuing session",
                suggestions=["Provide a prompt", "Use continue_session=True with session_id"]
            )
        
        # Output format for parsing
        cmd.extend(["--output-format", "stream-json"])
        cmd.extend(["--verbose"])  # Required for stream-json
        
        # Safety limits
        cmd.extend(["--max-turns", str(self.config.max_turns)])
        
        # Add allowed tools if configured
        if self.config.allowed_tools:
            cmd.extend(["--allowedTools", ",".join(self.config.allowed_tools)])
        
        logger.debug(
            "Built Claude command",
            command_length=len(cmd),
            has_session=bool(session_id),
            continue_session=continue_session,
        )
        
        return cmd
    
    async def _start_process(self, cmd: List[str], cwd: Path) -> Process:
        """Start Claude CLI subprocess with proper configuration.
        
        Args:
            cmd: Command to execute
            cwd: Working directory
            
        Returns:
            Started Process object
            
        Raises:
            ClaudeCLIError: If process startup fails
        """
        try:
            # Prepare environment
            env = self._prepare_environment()
            
            # Start process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(cwd),
                env=env,
                limit=1024 * 1024 * 512,  # 512MB memory limit
            )
            
            logger.debug(
                "Started Claude process",
                pid=process.pid,
                cwd=str(cwd),
            )
            
            return process
            
        except Exception as e:
            raise ClaudeCLIError(
                f"Failed to start Claude process: {str(e)}",
                command=cmd,
                suggestions=[
                    "Check Claude CLI installation",
                    "Verify working directory exists",
                    "Check system resources",
                    "Verify permissions",
                ]
            )
    
    async def _handle_process_output(
        self,
        process: Process,
        stream_callback: Optional[Callable],
        process_id: str,
    ) -> CLIResponse:
        """Handle Claude process output with streaming and parsing.
        
        Args:
            process: Running Claude process
            stream_callback: Optional callback for streaming updates
            process_id: Process identifier for logging
            
        Returns:
            Parsed CLIResponse
            
        Raises:
            ClaudeParsingError: If output parsing fails
            ClaudeCLIError: If process fails
        """
        message_buffer = deque(maxlen=self.max_message_buffer)
        parsing_errors = []
        result_message = None
        
        try:
            # Process streaming output
            async for line in self._read_stream_bounded(process.stdout):
                if not line.strip():
                    continue
                    
                try:
                    # Parse JSON message
                    msg = json.loads(line)
                    
                    # Validate message structure
                    if not self._validate_message(msg):
                        parsing_errors.append(f"Invalid message: {line[:100]}")
                        continue
                    
                    message_buffer.append(msg)
                    
                    # Handle streaming callback
                    if stream_callback:
                        update = self._create_stream_update(msg)
                        if update:
                            try:
                                await stream_callback(update)
                            except Exception as e:
                                logger.warning(
                                    "Stream callback failed",
                                    error=str(e),
                                    update_type=update.type,
                                    process_id=process_id,
                                )
                    
                    # Check for final result
                    if msg.get("type") == "result":
                        result_message = msg
                        
                except json.JSONDecodeError as e:
                    parsing_errors.append(f"JSON error: {str(e)}")
                    logger.debug(
                        "JSON parsing failed",
                        line=line[:200],
                        error=str(e),
                        process_id=process_id,
                    )
                    continue
            
            # Wait for process completion
            return_code = await process.wait()
            
            # Handle process errors
            if return_code != 0:
                stderr = await process.stderr.read()
                stderr_text = stderr.decode("utf-8", errors="replace")
                
                logger.error(
                    "Claude process failed",
                    return_code=return_code,
                    stderr=stderr_text[:500],
                    process_id=process_id,
                )
                
                # Handle specific error types
                error_msg = self._parse_error_message(stderr_text, return_code)
                raise ClaudeCLIError(
                    error_msg,
                    exit_code=return_code,
                    stderr=stderr_text,
                )
            
            # Parse final result
            if not result_message:
                logger.error(
                    "No result message received",
                    message_count=len(message_buffer),
                    parsing_errors=len(parsing_errors),
                    process_id=process_id,
                )
                
                raise ClaudeParsingError(
                    "No result message in Claude output",
                    parse_stage="result_extraction",
                    raw_data=f"Messages: {len(message_buffer)}, Errors: {len(parsing_errors)}",
                    suggestions=[
                        "Try the request again",
                        "Use simpler prompts",
                        "Check Claude CLI version",
                        "Enable debug logging",
                    ]
                )
            
            # Build response
            response = self._parse_result_message(
                result_message,
                list(message_buffer),
                parsing_errors,
            )
            
            logger.debug(
                "Parsed Claude response",
                content_length=len(response.content),
                cost=response.cost,
                tools_used=len(response.tools_used),
                parsing_errors=len(parsing_errors),
                process_id=process_id,
            )
            
            return response
            
        except Exception as e:
            if isinstance(e, (ClaudeCLIError, ClaudeParsingError)):
                raise
            else:
                logger.error(
                    "Unexpected error in output handling",
                    error=str(e),
                    error_type=type(e).__name__,
                    process_id=process_id,
                )
                
                raise ClaudeParsingError(
                    f"Output processing failed: {str(e)}",
                    parse_stage="output_processing",
                    suggestions=[
                        "Try the request again",
                        "Check system resources",
                        "Review debug logs",
                        "Report issue if persistent",
                    ]
                )
    
    async def _read_stream_bounded(self, stream) -> AsyncIterator[str]:
        """Read stream with memory bounds to prevent excessive usage.
        
        Args:
            stream: Stream to read from
            
        Yields:
            Individual lines from the stream
        """
        buffer = b""
        
        while True:
            try:
                chunk = await stream.read(self.streaming_buffer_size)
                if not chunk:
                    break
                
                buffer += chunk
                
                # Process complete lines
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    yield line.decode("utf-8", errors="replace").strip()
                    
            except Exception as e:
                logger.warning("Stream reading error", error=str(e))
                break
        
        # Process remaining buffer
        if buffer:
            yield buffer.decode("utf-8", errors="replace").strip()
    
    def _validate_message(self, msg: Dict[str, Any]) -> bool:
        """Validate JSON message structure from Claude CLI.
        
        Args:
            msg: Parsed JSON message
            
        Returns:
            True if message is valid
        """
        if not isinstance(msg, dict):
            return False
        
        # Must have a type field
        if "type" not in msg:
            return False
        
        # Type must be string
        if not isinstance(msg["type"], str):
            return False
        
        return True
    
    def _create_stream_update(self, msg: Dict[str, Any]) -> Optional[StreamUpdate]:
        """Create StreamUpdate from Claude CLI message.
        
        Args:
            msg: Parsed JSON message from Claude
            
        Returns:
            StreamUpdate object or None if message type unknown
        """
        msg_type = msg.get("type")
        
        if msg_type == "assistant":
            return self._parse_assistant_message(msg)
        elif msg_type == "user":
            return self._parse_user_message(msg)
        elif msg_type == "system":
            return self._parse_system_message(msg)
        elif msg_type == "tool_result":
            return self._parse_tool_result_message(msg)
        elif msg_type == "error":
            return self._parse_error_update(msg)
        elif msg_type == "progress":
            return self._parse_progress_message(msg)
        else:
            # Unknown message type
            logger.debug("Unknown message type", msg_type=msg_type)
            return None
    
    def _parse_assistant_message(self, msg: Dict[str, Any]) -> StreamUpdate:
        """Parse assistant message for streaming."""
        message = msg.get("message", {})
        content_blocks = message.get("content", [])
        
        text_content = []
        tool_calls = []
        
        for block in content_blocks:
            if block.get("type") == "text":
                text_content.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                tool_calls.append({
                    "name": block.get("name"),
                    "input": block.get("input", {}),
                    "id": block.get("id"),
                })
        
        return StreamUpdate(
            type=StreamType.ASSISTANT,
            content="\n".join(text_content) if text_content else None,
            tool_calls=tool_calls if tool_calls else None,
            session_id=msg.get("session_id"),
            metadata={"message_id": msg.get("id")},
        )
    
    def _parse_user_message(self, msg: Dict[str, Any]) -> StreamUpdate:
        """Parse user message for streaming."""
        message = msg.get("message", {})
        content = message.get("content", "")
        
        # Handle both string and list formats
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    text_parts.append(block)
            content = "\n".join(text_parts)
        
        return StreamUpdate(
            type=StreamType.USER,
            content=content,
            session_id=msg.get("session_id"),
            metadata={"message_id": msg.get("id")},
        )
    
    def _parse_system_message(self, msg: Dict[str, Any]) -> StreamUpdate:
        """Parse system message for streaming."""
        return StreamUpdate(
            type=StreamType.SYSTEM,
            content=msg.get("message", str(msg)),
            session_id=msg.get("session_id"),
            metadata={
                "subtype": msg.get("subtype"),
                "tools": msg.get("tools"),
                "model": msg.get("model"),
                "cwd": msg.get("cwd"),
            },
        )
    
    def _parse_tool_result_message(self, msg: Dict[str, Any]) -> StreamUpdate:
        """Parse tool result message for streaming."""
        result = msg.get("result", {})
        content = result.get("content") if isinstance(result, dict) else str(result)
        
        return StreamUpdate(
            type=StreamType.TOOL_RESULT,
            content=content,
            session_id=msg.get("session_id"),
            metadata={
                "tool_use_id": msg.get("tool_use_id"),
                "is_error": result.get("is_error", False) if isinstance(result, dict) else False,
                "execution_time_ms": result.get("execution_time_ms") if isinstance(result, dict) else None,
            },
        )
    
    def _parse_error_update(self, msg: Dict[str, Any]) -> StreamUpdate:
        """Parse error message for streaming."""
        error_message = msg.get("message", msg.get("error", str(msg)))
        
        return StreamUpdate(
            type=StreamType.ERROR,
            content=error_message,
            session_id=msg.get("session_id"),
            error_info={
                "message": error_message,
                "code": msg.get("code"),
                "subtype": msg.get("subtype"),
            },
        )
    
    def _parse_progress_message(self, msg: Dict[str, Any]) -> StreamUpdate:
        """Parse progress message for streaming."""
        return StreamUpdate(
            type=StreamType.PROGRESS,
            content=msg.get("message", msg.get("status")),
            session_id=msg.get("session_id"),
            progress={
                "percentage": msg.get("percentage"),
                "step": msg.get("step"),
                "total_steps": msg.get("total_steps"),
                "operation": msg.get("operation"),
            },
        )
    
    def _parse_result_message(
        self,
        result_msg: Dict[str, Any],
        messages: List[Dict[str, Any]], 
        parsing_errors: List[str],
    ) -> CLIResponse:
        """Parse final result message into CLIResponse.
        
        Args:
            result_msg: Final result message from Claude
            messages: All messages from the session
            parsing_errors: Any parsing errors encountered
            
        Returns:
            CLIResponse with parsed data
        """
        # Extract tools used from messages
        tools_used = []
        for msg in messages:
            if msg.get("type") == "assistant":
                message = msg.get("message", {})
                for block in message.get("content", []):
                    if block.get("type") == "tool_use":
                        tools_used.append({
                            "name": block.get("name"),
                            "timestamp": msg.get("timestamp"),
                            "input": block.get("input", {}),
                            "id": block.get("id"),
                        })
        
        # Extract content
        content = result_msg.get("result", "")
        if not content and messages:
            # Fallback: extract from assistant messages
            content_parts = []
            for msg in messages:
                if msg.get("type") == "assistant":
                    message = msg.get("message", {})
                    for block in message.get("content", []):
                        if block.get("type") == "text":
                            content_parts.append(block.get("text", ""))
            content = "\n".join(content_parts)
        
        return CLIResponse(
            content=content,
            session_id=result_msg.get("session_id", ""),
            cost=result_msg.get("cost_usd", 0.0),
            duration_ms=result_msg.get("duration_ms", 0),
            num_turns=result_msg.get("num_turns", 0),
            is_error=result_msg.get("is_error", False),
            error_type=result_msg.get("subtype") if result_msg.get("is_error") else None,
            tools_used=tools_used,
            raw_messages=messages,
        )
    
    def _parse_error_message(self, stderr: str, exit_code: int) -> str:
        """Parse error message from stderr and exit code.
        
        Args:
            stderr: Standard error output
            exit_code: Process exit code
            
        Returns:
            User-friendly error message
        """
        stderr_lower = stderr.lower()
        
        # Usage limit error
        if "usage limit reached" in stderr_lower:
            # Try to extract reset time
            import re
            time_match = re.search(r"reset at (\d+[apm]+)", stderr, re.IGNORECASE)
            timezone_match = re.search(r"\(([^)]+)\)", stderr)
            
            reset_time = time_match.group(1) if time_match else "later"
            timezone = timezone_match.group(1) if timezone_match else ""
            
            return (
                f"🕒 Claude usage limit reached\n\n"
                f"Your limit will reset at {reset_time}"
                f"{f' ({timezone})' if timezone else ''}\n\n"
                f"Try again after the reset time or use simpler requests."
            )
        
        # Authentication errors
        elif any(phrase in stderr_lower for phrase in ["not authenticated", "invalid api key", "login required"]):
            return (
                "🔐 Authentication required\n\n"
                "Please run: claude auth login"
            )
        
        # CLI not found
        elif exit_code == 127 or "command not found" in stderr_lower:
            return (
                "🚫 Claude CLI not found\n\n"
                "Install with: npm install -g @anthropic-ai/claude-code"
            )
        
        # Permission errors
        elif "permission" in stderr_lower:
            return (
                "🔒 Permission denied\n\n"
                "Check file and directory permissions."
            )
        
        # Network errors
        elif any(phrase in stderr_lower for phrase in ["network", "connection", "timeout"]):
            return (
                "🌐 Network error\n\n"
                "Check your internet connection and try again."
            )
        
        # Generic error
        else:
            return f"Claude CLI error (exit code {exit_code}): {stderr.strip()}"
    
    def _prepare_environment(self) -> Dict[str, str]:
        """Prepare environment variables for Claude CLI.
        
        Returns:
            Environment dictionary
        """
        env = os.environ.copy()
        
        # Add configured environment variables
        env.update(self.config.environment_vars)
        
        # Ensure PATH includes Claude CLI directory if configured
        if self.config.claude_cli_path:
            claude_dir = str(Path(self.config.claude_cli_path).parent)
            current_path = env.get("PATH", "")
            if claude_dir not in current_path:
                env["PATH"] = f"{claude_dir}:{current_path}"
        
        return env