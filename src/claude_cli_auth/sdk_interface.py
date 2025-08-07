"""Claude Code SDK interface with CLI authentication.

This module provides integration with the Claude Code Python SDK while using
CLI-based authentication. It handles SDK initialization, streaming, error
handling, and fallback scenarios when SDK operations fail.
"""

import asyncio
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from .auth_manager import AuthManager
from .exceptions import ClaudeAuthError, ClaudeConfigError, ClaudeParsingError
from .models import AuthConfig, ClaudeResponse, StreamType, StreamUpdate

logger = logging.getLogger(__name__)

# SDK imports with graceful fallback
try:
    from claude_code_sdk import (
        ClaudeCodeOptions,
        ClaudeSDKError,
        CLIConnectionError,
        CLINotFoundError,
        Message,
        ProcessError,
        query,
    )
    from claude_code_sdk.types import (
        AssistantMessage,
        ResultMessage,
        ToolUseBlock,
        UserMessage,
    )
    SDK_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Claude Code SDK not available: {str(e)} (Install with: pip install claude-code-sdk)")
    SDK_AVAILABLE = False
    
    # Mock classes for type hints when SDK not available
    class ClaudeCodeOptions: pass
    class ClaudeSDKError(Exception): pass
    class CLIConnectionError(Exception): pass
    class CLINotFoundError(Exception): pass
    class ProcessError(Exception): pass
    class Message: pass
    class AssistantMessage: pass
    class ResultMessage: pass
    class ToolUseBlock: pass
    class UserMessage: pass


@dataclass
class SDKResponse:
    """Response from Claude Code SDK execution."""
    
    content: str
    session_id: str
    cost: float = 0.0
    duration_ms: int = 0
    num_turns: int = 0
    is_error: bool = False
    error_type: Optional[str] = None
    tools_used: List[Dict[str, Any]] = field(default_factory=list)
    model_info: Optional[Dict[str, Any]] = None
    raw_messages: List[Any] = field(default_factory=list)
    
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
            model_info=self.model_info,
            created_at=time.time(),
        )


class SDKInterface:
    """Interface to Claude Code Python SDK with CLI authentication.
    
    Provides SDK-based Claude integration with the following features:
    - CLI authentication integration (no API keys needed)
    - Streaming response handling
    - Comprehensive error handling and recovery
    - Graceful fallback when SDK unavailable
    - Performance optimization and monitoring
    
    Example:
        ```python
        # Basic usage
        sdk = SDKInterface()
        response = await sdk.execute(
            prompt="Hello Claude",
            working_directory=Path(".")
        )
        
        # With streaming
        async def on_stream(update):
            print(f"[{update.type}] {update.content}")
        
        response = await sdk.execute(
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
        """Initialize SDK interface.
        
        Args:
            config: Configuration for SDK operations
            auth_manager: Authentication manager instance
            
        Raises:
            ClaudeConfigError: If SDK is not available or configuration invalid
            ClaudeAuthError: If authentication setup fails
        """
        if not SDK_AVAILABLE:
            raise ClaudeConfigError(
                "Claude Code SDK is not available",
                config_field="sdk_dependency",
                suggestions=[
                    "Install SDK: pip install claude-code-sdk",
                    "Use CLI interface instead",
                    "Check installation documentation",
                ]
            )
        
        self.config = config or AuthConfig()
        self.auth_manager = auth_manager or AuthManager(self.config)
        
        # SDK session tracking
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self._sdk_failed_count = 0
        
        # Performance monitoring
        self._total_requests = 0
        self._total_errors = 0
        self._total_cost = 0.0
        
        # Initialize SDK environment
        self._setup_sdk_environment()
        
        logger.info(
            f"SDK interface initialized - config_dir: {str(self.config.claude_config_dir)}, "
            f"timeout: {self.config.timeout_seconds}, use_streaming: {self.config.enable_streaming}"
        )
    
    async def execute(
        self,
        prompt: str,
        working_directory: Optional[Path] = None,
        session_id: Optional[str] = None,
        continue_session: bool = False,
        stream_callback: Optional[Callable[[StreamUpdate], None]] = None,
        timeout: Optional[float] = None,
    ) -> SDKResponse:
        """Execute Claude query via SDK with comprehensive error handling.
        
        Args:
            prompt: Prompt to send to Claude
            working_directory: Directory to run command in
            session_id: Session ID for conversation continuity
            continue_session: Whether to continue existing session
            stream_callback: Callback for streaming updates
            timeout: Command timeout in seconds
            
        Returns:
            SDKResponse with execution results
            
        Raises:
            ClaudeAuthError: If authentication fails
            ClaudeSDKError: If SDK execution fails
            ClaudeParsingError: If response parsing fails
        """
        start_time = time.time()
        execution_id = str(uuid.uuid4())
        
        # Update counters
        self._total_requests += 1
        
        # Use provided working directory or default
        work_dir = working_directory or self.config.working_directory
        
        logger.info(
            f"Executing Claude SDK query - execution_id: {execution_id}, "
            f"working_directory: {str(work_dir)}, session_id: {session_id}, "
            f"continue_session: {continue_session}, prompt_length: {len(prompt)}"
        )
        
        try:
            # Verify authentication before proceeding
            if not self.auth_manager.is_authenticated():
                raise ClaudeAuthError(
                    "Claude CLI not authenticated for SDK use",
                    error_code="SDK_AUTH_REQUIRED",
                    suggestions=[
                        "Run 'claude auth login'",
                        "Verify Claude CLI installation",
                        "Check internet connectivity",
                    ]
                )
            
            # Build SDK options
            options = self._build_sdk_options(work_dir)
            
            # Execute query with streaming
            messages = []
            cost = 0.0
            
            await asyncio.wait_for(
                self._execute_query_with_streaming(
                    prompt=prompt,
                    options=options,
                    messages=messages,
                    stream_callback=stream_callback,
                    execution_id=execution_id,
                ),
                timeout=timeout or self.config.timeout_seconds,
            )
            
            # Extract results from messages
            result = self._extract_results_from_messages(messages)
            
            # Calculate execution time
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Generate session ID if needed
            final_session_id = session_id or result.get("session_id") or f"sdk_{int(time.time())}_{execution_id[:8]}"
            
            # Build response
            response = SDKResponse(
                content=result.get("content", ""),
                session_id=final_session_id,
                cost=result.get("cost", 0.0),
                duration_ms=duration_ms,
                num_turns=result.get("num_turns", 0),
                tools_used=result.get("tools_used", []),
                model_info=result.get("model_info"),
                raw_messages=messages,
            )
            
            # Update session tracking
            self._update_session(final_session_id, messages)
            
            # Update statistics
            self._total_cost += response.cost
            
            logger.info(
                f"Claude SDK query completed - execution_id: {execution_id}, "
                f"session_id: {response.session_id}, duration_ms: {response.duration_ms}, "
                f"cost: {response.cost}, tools_used: {len(response.tools_used)}"
            )
            
            return response
            
        except asyncio.TimeoutError:
            self._total_errors += 1
            timeout_val = timeout or self.config.timeout_seconds
            
            logger.error(
                f"Claude SDK query timed out - execution_id: {execution_id}, "
                f"timeout_seconds: {timeout_val}"
            )
            
            raise ClaudeAuthError(
                f"Claude SDK timed out after {timeout_val}s",
                error_code="SDK_TIMEOUT",
                details={"timeout": timeout_val, "execution_id": execution_id},
                suggestions=[
                    "Increase timeout value",
                    "Try smaller prompts",
                    "Check Claude service availability",
                    "Use CLI interface as fallback",
                ]
            )
            
        except CLINotFoundError as e:
            self._total_errors += 1
            self._sdk_failed_count += 1
            
            logger.error(f"Claude CLI not found for SDK - error: {str(e)}")
            
            raise ClaudeConfigError(
                "Claude Code CLI not found for SDK integration",
                config_field="claude_cli_path",
                suggestions=[
                    "Install Claude CLI: npm install -g @anthropic-ai/claude-code",
                    "Add Claude CLI to PATH",
                    "Set claude_cli_path in configuration",
                    "Use CLI interface directly",
                ]
            )
            
        except ProcessError as e:
            self._total_errors += 1
            self._sdk_failed_count += 1
            
            logger.error(
                f"Claude SDK process error - error: {str(e)}, "
                f"exit_code: {getattr(e, 'exit_code', None)}"
            )
            
            raise ClaudeAuthError(
                f"Claude SDK process failed: {str(e)}",
                error_code="SDK_PROCESS_ERROR",
                suggestions=[
                    "Verify Claude CLI authentication",
                    "Check working directory permissions",
                    "Try CLI interface as fallback",
                    "Check system resources",
                ]
            )
            
        except CLIConnectionError as e:
            self._total_errors += 1
            self._sdk_failed_count += 1
            
            logger.error(f"Claude SDK connection error - error: {str(e)}")
            
            raise ClaudeAuthError(
                f"Failed to connect to Claude via SDK: {str(e)}",
                error_code="SDK_CONNECTION_ERROR",
                suggestions=[
                    "Check internet connectivity",
                    "Verify Claude service status",
                    "Try again in a moment",
                    "Use CLI interface as fallback",
                ]
            )
            
        except ClaudeSDKError as e:
            self._total_errors += 1
            self._sdk_failed_count += 1
            
            logger.error(f"Claude SDK error - error: {str(e)}")
            
            raise ClaudeAuthError(
                f"Claude SDK error: {str(e)}",
                error_code="SDK_ERROR",
                suggestions=[
                    "Check SDK version compatibility",
                    "Verify authentication status",
                    "Try CLI interface as fallback",
                    "Report issue if persistent",
                ]
            )
            
        except Exception as e:
            self._total_errors += 1
            
            # Handle ExceptionGroup from TaskGroup operations (Python 3.11+)
            if type(e).__name__ == "ExceptionGroup" or hasattr(e, "exceptions"):
                logger.error(
                    f"Task group error in Claude SDK - error: {str(e)}, "
                    f"error_type: {type(e).__name__}, "
                    f"exception_count: {len(getattr(e, 'exceptions', []))}"
                )
                
                # Extract main exception
                exceptions = getattr(e, "exceptions", [e])
                main_exception = exceptions[0] if exceptions else e
                
                raise ClaudeParsingError(
                    f"Claude SDK task error: {str(main_exception)}",
                    parse_stage="sdk_execution",
                    suggestions=[
                        "Try the request again",
                        "Use CLI interface as fallback",
                        "Check Python version compatibility",
                        "Report issue if persistent",
                    ]
                )
            else:
                logger.error(
                    f"Unexpected SDK error - error: {str(e)}, "
                    f"error_type: {type(e).__name__}, execution_id: {execution_id}"
                )
                
                raise ClaudeAuthError(
                    f"Unexpected SDK error: {str(e)}",
                    error_code="SDK_UNEXPECTED_ERROR",
                    suggestions=[
                        "Try the request again",
                        "Use CLI interface as fallback",
                        "Check debug logs",
                        "Report issue if persistent",
                    ]
                )
    
    async def kill_all_processes(self) -> None:
        """Clean up SDK sessions (no actual processes to kill)."""
        logger.info(f"Clearing SDK sessions - count: {len(self.active_sessions)}")
        self.active_sessions.clear()
    
    def get_active_process_count(self) -> int:
        """Get number of active SDK sessions."""
        return len(self.active_sessions)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get SDK interface statistics."""
        success_rate = (
            (self._total_requests - self._total_errors) / self._total_requests
            if self._total_requests > 0 else 0.0
        )
        
        return {
            "total_requests": self._total_requests,
            "total_errors": self._total_errors,
            "sdk_failures": self._sdk_failed_count,
            "success_rate": success_rate,
            "total_cost": self._total_cost,
            "active_sessions": len(self.active_sessions),
            "avg_cost_per_request": (
                self._total_cost / self._total_requests
                if self._total_requests > 0 else 0.0
            ),
        }
    
    def _setup_sdk_environment(self) -> None:
        """Set up environment for Claude Code SDK.
        
        Raises:
            ClaudeAuthError: If environment setup fails
        """
        try:
            # Don't set API key - use CLI authentication instead
            # The SDK will automatically use CLI credentials when no API key is provided
            
            # Update PATH for Claude CLI if configured
            if self.config.claude_cli_path:
                claude_dir = str(Path(self.config.claude_cli_path).parent)
                current_path = os.environ.get("PATH", "")
                if claude_dir not in current_path:
                    os.environ["PATH"] = f"{claude_dir}:{current_path}"
                    logger.debug(f"Updated PATH for Claude CLI - claude_dir: {claude_dir}")
            
            # Set additional environment variables
            for key, value in self.config.environment_vars.items():
                os.environ[key] = value
            
            logger.debug("SDK environment configured successfully")
            
        except Exception as e:
            raise ClaudeAuthError(
                f"Failed to setup SDK environment: {str(e)}",
                error_code="SDK_ENV_SETUP_ERROR",
                suggestions=[
                    "Check Claude CLI installation",
                    "Verify environment variable permissions",
                    "Review configuration settings",
                ]
            )
    
    def _build_sdk_options(self, working_directory: Path) -> ClaudeCodeOptions:
        """Build Claude Code SDK options.
        
        Args:
            working_directory: Working directory for execution
            
        Returns:
            Configured ClaudeCodeOptions
        """
        return ClaudeCodeOptions(
            max_turns=self.config.max_turns,
            cwd=str(working_directory),
            allowed_tools=self.config.allowed_tools,
        )
    
    async def _execute_query_with_streaming(
        self,
        prompt: str,
        options: ClaudeCodeOptions,
        messages: List[Any],
        stream_callback: Optional[Callable],
        execution_id: str,
    ) -> None:
        """Execute SDK query with streaming support.
        
        Args:
            prompt: User prompt
            options: SDK options
            messages: List to collect messages
            stream_callback: Optional streaming callback
            execution_id: Execution identifier for logging
        """
        try:
            async for message in query(prompt=prompt, options=options):
                messages.append(message)
                
                # Handle streaming callback
                if stream_callback and self.config.enable_streaming:
                    try:
                        update = self._create_stream_update_from_sdk_message(message)
                        if update:
                            await stream_callback(update)
                    except Exception as callback_error:
                        logger.warning(
                            f"Stream callback failed - error: {str(callback_error)}, "
                            f"error_type: {type(callback_error).__name__}, "
                            f"execution_id: {execution_id}"
                        )
                        # Continue processing even if callback fails
                        
        except Exception as e:
            logger.error(
                f"Error in SDK streaming execution - error: {str(e)}, "
                f"error_type: {type(e).__name__}, execution_id: {execution_id}"
            )
            # Re-raise to be handled by caller
            raise
    
    def _create_stream_update_from_sdk_message(self, message: Any) -> Optional[StreamUpdate]:
        """Create StreamUpdate from SDK message.
        
        Args:
            message: Message from Claude Code SDK
            
        Returns:
            StreamUpdate object or None
        """
        try:
            if isinstance(message, AssistantMessage):
                # Extract content from assistant message
                content = getattr(message, "content", [])
                text_parts = []
                tool_calls = []
                
                if content and isinstance(content, list):
                    for block in content:
                        if hasattr(block, "text"):
                            text_parts.append(block.text)
                        elif isinstance(block, ToolUseBlock):
                            tool_calls.append({
                                "name": getattr(block, "tool_name", "unknown"),
                                "input": getattr(block, "tool_input", {}),
                                "id": getattr(block, "id", str(uuid.uuid4())),
                            })
                elif content:
                    text_parts.append(str(content))
                
                return StreamUpdate(
                    type=StreamType.ASSISTANT,
                    content="\n".join(text_parts) if text_parts else None,
                    tool_calls=tool_calls if tool_calls else None,
                )
                
            elif isinstance(message, UserMessage):
                content = getattr(message, "content", "")
                return StreamUpdate(
                    type=StreamType.USER,
                    content=str(content) if content else None,
                )
                
            elif isinstance(message, ResultMessage):
                return StreamUpdate(
                    type=StreamType.RESULT,
                    content="Query completed",
                    metadata={
                        "cost": getattr(message, "total_cost_usd", 0.0),
                        "turns": getattr(message, "num_turns", 0),
                    },
                )
                
        except Exception as e:
            logger.warning(
                f"Failed to create stream update from SDK message - "
                f"error: {str(e)}, message_type: {type(message).__name__}"
            )
        
        return None
    
    def _extract_results_from_messages(self, messages: List[Any]) -> Dict[str, Any]:
        """Extract results from SDK messages.
        
        Args:
            messages: List of SDK messages
            
        Returns:
            Dictionary with extracted results
        """
        content_parts = []
        tools_used = []
        cost = 0.0
        num_turns = 0
        model_info = None
        
        for message in messages:
            if isinstance(message, AssistantMessage):
                content = getattr(message, "content", [])
                if content and isinstance(content, list):
                    for block in content:
                        if hasattr(block, "text"):
                            content_parts.append(block.text)
                        elif isinstance(block, ToolUseBlock):
                            tools_used.append({
                                "name": getattr(block, "tool_name", "unknown"),
                                "timestamp": time.time(),
                                "input": getattr(block, "tool_input", {}),
                                "id": getattr(block, "id", str(uuid.uuid4())),
                            })
                elif content:
                    content_parts.append(str(content))
                    
            elif isinstance(message, ResultMessage):
                cost = getattr(message, "total_cost_usd", 0.0) or 0.0
                num_turns = getattr(message, "num_turns", 0) or 0
                
                # Extract model info if available
                if hasattr(message, "model"):
                    model_info = {"model": getattr(message, "model")}
        
        return {
            "content": "\n".join(content_parts),
            "cost": cost,
            "num_turns": num_turns,
            "tools_used": tools_used,
            "model_info": model_info,
        }
    
    def _update_session(self, session_id: str, messages: List[Any]) -> None:
        """Update session tracking data.
        
        Args:
            session_id: Session identifier
            messages: Messages from this session
        """
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                "messages": [],
                "created_at": time.time(),
            }
        
        session_data = self.active_sessions[session_id]
        session_data["messages"] = messages
        session_data["last_used"] = time.time()
        
        # Limit session size for memory management
        max_messages = 100
        if len(session_data["messages"]) > max_messages:
            session_data["messages"] = session_data["messages"][-max_messages:]
        
        logger.debug(
            f"Updated SDK session - session_id: {session_id}, "
            f"message_count: {len(messages)}"
        )