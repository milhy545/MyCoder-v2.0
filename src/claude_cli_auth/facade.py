"""Main facade for Claude CLI authentication with intelligent fallbacks.

This module provides the primary interface for Claude AI integration, implementing
a sophisticated fallback system that tries SDK first, then CLI, with comprehensive
error handling and recovery mechanisms.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from .auth_manager import AuthManager
from .cli_interface import CLIInterface
from .exceptions import (
    ClaudeAuthError,
    ClaudeAuthManagerError,
    ClaudeCLIError,
    ClaudeConfigError,
    ClaudeNetworkError,
    ClaudeParsingError,
    ClaudeRateLimitError,
    ClaudeSessionError,
    ClaudeTimeoutError,
)
from .models import AuthConfig, ClaudeResponse, SessionInfo, StreamUpdate
from .sdk_interface import SDKInterface, SDK_AVAILABLE

logger = logging.getLogger(__name__)


class ClaudeAuthManager:
    """Main interface for Claude AI with CLI authentication and intelligent fallbacks.
    
    This is the primary class users should interact with. It provides:
    - Unified interface for Claude AI queries
    - Intelligent SDK → CLI fallback system
    - Comprehensive session management
    - Error handling and recovery
    - Performance monitoring and statistics
    - Graceful degradation when services fail
    
    Example:
        Basic usage:
        ```python
        claude = ClaudeAuthManager()
        
        response = await claude.query(
            "Explain this code",
            working_directory=Path(".")
        )
        
        print(response.content)
        print(f"Cost: ${response.cost:.4f}")
        ```
        
        With streaming and session management:
        ```python
        async def on_stream(update):
            print(f"[{update.type}] {update.content}")
        
        response = await claude.query(
            "Create a Python function",
            working_directory=Path("./src"),
            stream_callback=on_stream,
            session_id="my-project-session"
        )
        
        # Continue the conversation
        response2 = await claude.query(
            "Add error handling to that function",
            session_id="my-project-session",
            continue_session=True
        )
        ```
        
        Session management:
        ```python
        # List all sessions
        sessions = claude.list_sessions()
        
        # Get session details
        session = claude.get_session("my-project-session")
        if session:
            print(f"Total cost: ${session.total_cost:.4f}")
            print(f"Messages: {session.total_turns}")
        
        # Clean up old sessions
        cleaned = await claude.cleanup_sessions()
        print(f"Cleaned {cleaned} expired sessions")
        ```
    """
    
    def __init__(
        self,
        config: Optional[AuthConfig] = None,
        prefer_sdk: bool = True,
        enable_fallback: bool = True,
    ):
        """Initialize Claude authentication manager.
        
        Args:
            config: Configuration for Claude operations
            prefer_sdk: Whether to prefer SDK over CLI (default: True)
            enable_fallback: Whether to enable fallback between methods (default: True)
            
        Raises:
            ClaudeConfigError: If configuration is invalid
            ClaudeAuthError: If authentication setup fails
        """
        self.config = config or AuthConfig()
        self.prefer_sdk = prefer_sdk and SDK_AVAILABLE
        self.enable_fallback = enable_fallback
        
        # Initialize authentication manager
        try:
            self.auth_manager = AuthManager(self.config)
        except Exception as e:
            raise ClaudeAuthManagerError(
                f"Failed to initialize authentication: {str(e)}",
                error_code="AUTH_INIT_ERROR",
                suggestions=[
                    "Check Claude CLI installation",
                    "Verify authentication with 'claude auth login'",
                    "Check configuration settings",
                ]
            )
        
        # Initialize interfaces
        self.sdk_interface: Optional[SDKInterface] = None
        self.cli_interface: Optional[CLIInterface] = None
        
        # Initialize based on preferences and availability
        self._initialize_interfaces()
        
        # Fallback tracking
        self._sdk_failure_count = 0
        self._cli_failure_count = 0
        self._last_fallback_time = 0.0
        self._fallback_cooldown = 60.0  # seconds
        
        # Performance metrics
        self._stats = {
            "total_requests": 0,
            "sdk_requests": 0,
            "cli_requests": 0,
            "sdk_failures": 0,
            "cli_failures": 0,
            "fallback_successes": 0,
            "total_cost": 0.0,
            "total_duration_ms": 0,
        }
        
        logger.info(
            "ClaudeAuthManager initialized",
            prefer_sdk=self.prefer_sdk,
            enable_fallback=self.enable_fallback,
            sdk_available=self.sdk_interface is not None,
            cli_available=self.cli_interface is not None,
        )
    
    async def query(
        self,
        prompt: str,
        working_directory: Optional[Path] = None,
        session_id: Optional[str] = None,
        continue_session: bool = False,
        stream_callback: Optional[Callable[[StreamUpdate], None]] = None,
        timeout: Optional[float] = None,
        user_id: Optional[Union[str, int]] = None,
    ) -> ClaudeResponse:
        """Execute Claude query with intelligent fallback system.
        
        Args:
            prompt: Prompt to send to Claude
            working_directory: Working directory for the query
            session_id: Session ID for conversation continuity
            continue_session: Whether to continue existing session
            stream_callback: Callback for streaming updates
            timeout: Query timeout in seconds
            user_id: User identifier for session tracking
            
        Returns:
            ClaudeResponse with query results
            
        Raises:
            ClaudeAuthError: If authentication fails
            ClaudeTimeoutError: If query times out
            ClaudeAuthManagerError: If all methods fail
        """
        start_time = time.time()
        work_dir = working_directory or self.config.working_directory
        
        # Update stats
        self._stats["total_requests"] += 1
        
        # Get or create session if needed
        session = None
        if session_id or user_id:
            session = await self._get_or_create_session(
                session_id=session_id,
                user_id=user_id,
                working_directory=work_dir,
            )
            session_id = session.session_id
        
        logger.info(
            "Starting Claude query",
            session_id=session_id,
            continue_session=continue_session,
            prompt_length=len(prompt),
            working_directory=str(work_dir),
            user_id=user_id,
        )
        
        # Determine execution method
        primary_method, fallback_method = self._choose_execution_methods()
        
        # Execute with primary method
        response = None
        last_error = None
        
        for method_name, method in [(primary_method, "primary"), (fallback_method, "fallback")]:
            if method_name is None:
                continue
                
            try:
                logger.debug(f"Trying {method_name} method ({method})")
                
                response = await self._execute_with_method(
                    method_name=method_name,
                    prompt=prompt,
                    working_directory=work_dir,
                    session_id=session_id,
                    continue_session=continue_session,
                    stream_callback=stream_callback,
                    timeout=timeout,
                )
                
                # Success - update stats and break
                if method == "fallback":
                    self._stats["fallback_successes"] += 1
                    logger.info(f"Fallback to {method_name} succeeded")
                
                break
                
            except Exception as e:
                last_error = e
                
                # Log the error
                logger.warning(
                    f"{method_name} method failed ({method})",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                
                # Update failure counts
                if method_name == "sdk":
                    self._sdk_failure_count += 1
                    self._stats["sdk_failures"] += 1
                elif method_name == "cli":
                    self._cli_failure_count += 1
                    self._stats["cli_failures"] += 1
                
                # If this was the primary method and we have a fallback, continue
                if method == "primary" and fallback_method is not None and self.enable_fallback:
                    self._last_fallback_time = time.time()
                    continue
                else:
                    # No fallback available or this was the fallback - fail
                    break
        
        # Check if we got a response
        if response is None:
            # All methods failed
            error_msg = f"All Claude methods failed. Last error: {str(last_error)}"
            
            if isinstance(last_error, ClaudeTimeoutError):
                raise last_error
            elif isinstance(last_error, ClaudeAuthError):
                raise last_error
            else:
                raise ClaudeAuthManagerError(
                    error_msg,
                    error_code="ALL_METHODS_FAILED",
                    details={
                        "primary_method": primary_method,
                        "fallback_method": fallback_method,
                        "last_error": str(last_error),
                        "sdk_failures": self._sdk_failure_count,
                        "cli_failures": self._cli_failure_count,
                    },
                    suggestions=[
                        "Check Claude CLI authentication",
                        "Verify internet connectivity", 
                        "Try again with simpler prompt",
                        "Check system resources",
                        "Review debug logs for details",
                    ]
                )
        
        # Update session if we have one
        if session:
            self.auth_manager.update_session(
                session_id=session.session_id,
                cost=response.cost,
                turns=response.num_turns,
                tools_used=len(response.tools_used),
            )
        
        # Update stats
        execution_time = int((time.time() - start_time) * 1000)
        self._stats["total_cost"] += response.cost
        self._stats["total_duration_ms"] += execution_time
        
        logger.info(
            "Claude query completed",
            session_id=response.session_id,
            cost=response.cost,
            duration_ms=execution_time,
            method=primary_method if response else "failed",
            tools_used=len(response.tools_used),
        )
        
        return response
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionInfo if session exists, None otherwise
        """
        return self.auth_manager.get_session(session_id)
    
    def list_sessions(
        self,
        user_id: Optional[Union[str, int]] = None,
        include_expired: bool = False,
    ) -> List[SessionInfo]:
        """List sessions, optionally filtered by user.
        
        Args:
            user_id: Filter by user ID (None for all users)
            include_expired: Whether to include expired sessions
            
        Returns:
            List of SessionInfo objects
        """
        return self.auth_manager.list_sessions(user_id=user_id, include_expired=include_expired)
    
    async def cleanup_sessions(self) -> int:
        """Clean up expired sessions.
        
        Returns:
            Number of sessions removed
        """
        return self.auth_manager.cleanup_expired_sessions()
    
    def get_usage_summary(
        self, user_id: Optional[Union[str, int]] = None
    ) -> Dict[str, Any]:
        """Get usage summary for user or all users.
        
        Args:
            user_id: User to get summary for (None for all users)
            
        Returns:
            Dictionary with usage statistics
        """
        return self.auth_manager.get_usage_summary(user_id=user_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about Claude usage.
        
        Returns:
            Dictionary with performance and usage statistics
        """
        stats = self._stats.copy()
        
        # Calculate derived metrics
        if stats["total_requests"] > 0:
            stats["success_rate"] = (
                (stats["total_requests"] - stats["sdk_failures"] - stats["cli_failures"]) 
                / stats["total_requests"]
            )
            stats["avg_cost_per_request"] = stats["total_cost"] / stats["total_requests"]
            stats["avg_duration_ms"] = stats["total_duration_ms"] / stats["total_requests"]
        else:
            stats["success_rate"] = 0.0
            stats["avg_cost_per_request"] = 0.0
            stats["avg_duration_ms"] = 0.0
        
        # Add interface stats
        if self.sdk_interface:
            stats["sdk_stats"] = self.sdk_interface.get_stats()
        if self.cli_interface:
            stats["cli_active_processes"] = self.cli_interface.get_active_process_count()
        
        # Add authentication info
        try:
            auth_info = self.auth_manager.get_authentication_info()
            stats["authentication"] = {
                "authenticated": auth_info["authenticated"],
                "claude_cli_version": auth_info.get("claude_cli_version"),
                "error": auth_info.get("error"),
            }
        except Exception as e:
            stats["authentication"] = {"error": str(e)}
        
        return stats
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration.
        
        Returns:
            Dictionary with configuration settings
        """
        config_dict = self.config.to_dict()
        config_dict.update({
            "prefer_sdk": self.prefer_sdk,
            "enable_fallback": self.enable_fallback,
            "sdk_available": SDK_AVAILABLE,
            "sdk_interface_initialized": self.sdk_interface is not None,
            "cli_interface_initialized": self.cli_interface is not None,
        })
        return config_dict
    
    def is_healthy(self) -> bool:
        """Check if the manager is healthy and ready to handle requests.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Check authentication
            if not self.auth_manager.is_authenticated():
                return False
            
            # Check that we have at least one working interface
            if self.sdk_interface is None and self.cli_interface is None:
                return False
            
            # Check failure rates
            total_requests = self._stats["total_requests"]
            if total_requests > 10:  # Only check after some requests
                total_failures = self._stats["sdk_failures"] + self._stats["cli_failures"]
                failure_rate = total_failures / total_requests
                if failure_rate > 0.8:  # More than 80% failures
                    return False
            
            return True
            
        except Exception:
            return False
    
    async def shutdown(self) -> None:
        """Shutdown the manager and clean up resources."""
        logger.info("Shutting down ClaudeAuthManager")
        
        # Kill active processes
        if self.sdk_interface:
            await self.sdk_interface.kill_all_processes()
        if self.cli_interface:
            await self.cli_interface.kill_all_processes()
        
        # Clean up expired sessions
        await self.cleanup_sessions()
        
        logger.info("ClaudeAuthManager shutdown complete")
    
    def _initialize_interfaces(self) -> None:
        """Initialize SDK and CLI interfaces based on configuration."""
        # Try to initialize SDK interface
        if SDK_AVAILABLE and (self.prefer_sdk or self.enable_fallback):
            try:
                self.sdk_interface = SDKInterface(
                    config=self.config,
                    auth_manager=self.auth_manager,
                )
                logger.info("SDK interface initialized successfully")
            except Exception as e:
                logger.warning(
                    "Failed to initialize SDK interface",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                self.sdk_interface = None
        
        # Try to initialize CLI interface
        if not self.prefer_sdk or self.enable_fallback or self.sdk_interface is None:
            try:
                self.cli_interface = CLIInterface(
                    config=self.config,
                    auth_manager=self.auth_manager,
                )
                logger.info("CLI interface initialized successfully")
            except Exception as e:
                logger.warning(
                    "Failed to initialize CLI interface",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                self.cli_interface = None
        
        # Check that we have at least one interface
        if self.sdk_interface is None and self.cli_interface is None:
            raise ClaudeAuthManagerError(
                "Failed to initialize any Claude interface",
                error_code="NO_INTERFACES_AVAILABLE",
                suggestions=[
                    "Check Claude CLI installation and authentication",
                    "Install Claude Code SDK if using SDK features", 
                    "Verify system requirements and permissions",
                    "Check debug logs for specific errors",
                ]
            )
    
    def _choose_execution_methods(self) -> tuple[Optional[str], Optional[str]]:
        """Choose primary and fallback execution methods.
        
        Returns:
            Tuple of (primary_method, fallback_method) where each is 'sdk' or 'cli' or None
        """
        # Determine available methods
        available_methods = []
        if self.sdk_interface is not None:
            available_methods.append("sdk")
        if self.cli_interface is not None:
            available_methods.append("cli")
        
        if not available_methods:
            return None, None
        
        # Choose primary method
        if self.prefer_sdk and "sdk" in available_methods:
            primary = "sdk"
        elif "cli" in available_methods:
            primary = "cli"
        else:
            primary = available_methods[0]
        
        # Choose fallback method
        fallback = None
        if self.enable_fallback and len(available_methods) > 1:
            for method in available_methods:
                if method != primary:
                    # Check if this method is in cooldown due to recent failures
                    if not self._is_method_in_cooldown(method):
                        fallback = method
                        break
        
        return primary, fallback
    
    def _is_method_in_cooldown(self, method: str) -> bool:
        """Check if a method is in cooldown due to recent failures.
        
        Args:
            method: Method name ('sdk' or 'cli')
            
        Returns:
            True if method is in cooldown
        """
        if method == "sdk":
            failure_count = self._sdk_failure_count
        elif method == "cli":
            failure_count = self._cli_failure_count
        else:
            return False
        
        # If we haven't had many failures, no cooldown
        if failure_count < 3:
            return False
        
        # Check if enough time has passed since last fallback
        time_since_fallback = time.time() - self._last_fallback_time
        return time_since_fallback < self._fallback_cooldown
    
    async def _execute_with_method(
        self,
        method_name: str,
        prompt: str,
        working_directory: Path,
        session_id: Optional[str] = None,
        continue_session: bool = False,
        stream_callback: Optional[Callable] = None,
        timeout: Optional[float] = None,
    ) -> ClaudeResponse:
        """Execute query with specific method.
        
        Args:
            method_name: Method to use ('sdk' or 'cli')
            prompt: User prompt
            working_directory: Working directory
            session_id: Session ID
            continue_session: Whether to continue session
            stream_callback: Streaming callback
            timeout: Timeout in seconds
            
        Returns:
            ClaudeResponse from execution
            
        Raises:
            Various Claude exceptions depending on the error type
        """
        if method_name == "sdk" and self.sdk_interface:
            self._stats["sdk_requests"] += 1
            sdk_response = await self.sdk_interface.execute(
                prompt=prompt,
                working_directory=working_directory,
                session_id=session_id,
                continue_session=continue_session,
                stream_callback=stream_callback,
                timeout=timeout,
            )
            return sdk_response.to_claude_response()
            
        elif method_name == "cli" and self.cli_interface:
            self._stats["cli_requests"] += 1
            cli_response = await self.cli_interface.execute(
                prompt=prompt,
                working_directory=working_directory,
                session_id=session_id,
                continue_session=continue_session,
                stream_callback=stream_callback,
                timeout=timeout,
            )
            return cli_response.to_claude_response()
            
        else:
            raise ClaudeAuthManagerError(
                f"Method '{method_name}' is not available",
                error_code="METHOD_NOT_AVAILABLE",
                suggestions=[
                    "Check interface initialization",
                    "Verify Claude CLI installation",
                    "Install Claude Code SDK if needed",
                ]
            )
    
    async def _get_or_create_session(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[Union[str, int]] = None,
        working_directory: Optional[Path] = None,
    ) -> SessionInfo:
        """Get existing session or create new one.
        
        Args:
            session_id: Existing session ID
            user_id: User identifier
            working_directory: Working directory
            
        Returns:
            SessionInfo object
        """
        if session_id:
            # Try to get existing session
            session = self.auth_manager.get_session(session_id)
            if session:
                return session
        
        # Create new session
        return self.auth_manager.create_session(
            user_id=user_id,
            working_directory=working_directory,
            session_id=session_id,
        )