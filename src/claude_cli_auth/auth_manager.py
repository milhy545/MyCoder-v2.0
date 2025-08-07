"""Authentication and session management for Claude CLI.

This module handles Claude CLI authentication verification, session management,
credential storage, and configuration validation. It ensures that Claude CLI
is properly authenticated and manages session lifecycle.
"""

import json
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .exceptions import ClaudeAuthError, ClaudeConfigError, ClaudeSessionError
from .models import AuthConfig, SessionInfo, SessionStatus

logger = logging.getLogger(__name__)


class AuthManager:
    """Manages Claude CLI authentication and session state.
    
    This class handles:
    - Verifying Claude CLI authentication status
    - Managing session information and lifecycle  
    - Validating and storing configuration
    - Credential verification and management
    - Session cleanup and expiration
    
    Example:
        ```python
        auth = AuthManager()
        
        # Check authentication
        if not auth.is_authenticated():
            raise ClaudeAuthError("Please run: claude auth login")
        
        # Create session
        session = auth.create_session(user_id="user1")
        
        # Update session after use
        auth.update_session(session.session_id, cost=0.05, turns=2)
        ```
    """
    
    def __init__(self, config: Optional[AuthConfig] = None):
        """Initialize authentication manager.
        
        Args:
            config: Authentication configuration. If None, uses default config.
            
        Raises:
            ClaudeConfigError: If configuration is invalid
        """
        self.config = config or AuthConfig()
        
        # Validate configuration
        issues = self.config.validate()
        if issues:
            raise ClaudeConfigError(
                f"Configuration validation failed: {'; '.join(issues)}",
                config_field="multiple",
                suggestions=["Fix configuration issues", "Use default configuration"]
            )
        
        # Session storage
        self._sessions: Dict[str, SessionInfo] = {}
        self._session_file = self.config.claude_config_dir / "claude_cli_auth_sessions.json"
        
        # Load existing sessions
        self._load_sessions()
        
        logger.info(
            "AuthManager initialized", 
            config_dir=str(self.config.claude_config_dir),
            session_count=len(self._sessions)
        )
    
    def is_authenticated(self) -> bool:
        """Check if Claude CLI is authenticated.
        
        Verifies authentication by checking for credentials file and
        attempting to get authentication status from Claude CLI.
        
        Returns:
            True if Claude is authenticated, False otherwise
        """
        try:
            # Check for credentials file
            creds_file = self.config.claude_config_dir / ".credentials.json"
            if not creds_file.exists():
                logger.warning("Claude credentials file not found")
                return False
            
            # Try to get authentication status
            result = self._run_claude_command(["auth", "whoami"], timeout=10)
            
            # Check if command succeeded and didn't return error messages
            if result.returncode == 0:
                output = result.stdout.strip()
                # Common error patterns to check for
                error_patterns = [
                    "Invalid API key",
                    "Please run /login", 
                    "not authenticated",
                    "login required",
                ]
                
                for pattern in error_patterns:
                    if pattern.lower() in output.lower():
                        logger.warning("Authentication check failed", output=output)
                        return False
                
                logger.info("Claude authentication verified", user_info=output[:100])
                return True
            else:
                logger.warning(
                    "Claude auth command failed", 
                    returncode=result.returncode,
                    stderr=result.stderr.strip()
                )
                return False
                
        except Exception as e:
            logger.error("Error checking authentication", error=str(e))
            return False
    
    def get_authentication_info(self) -> Dict[str, Any]:
        """Get detailed authentication information.
        
        Returns:
            Dictionary with authentication status, user info, and diagnostics
            
        Raises:
            ClaudeAuthError: If unable to get authentication info
        """
        try:
            info = {
                "authenticated": False,
                "user_info": None,
                "config_dir": str(self.config.claude_config_dir),
                "credentials_file_exists": False,
                "claude_cli_version": None,
                "error": None,
            }
            
            # Check Claude CLI version
            try:
                result = self._run_claude_command(["--version"], timeout=5)
                if result.returncode == 0:
                    info["claude_cli_version"] = result.stdout.strip()
            except Exception as e:
                info["error"] = f"Claude CLI not accessible: {e}"
                return info
            
            # Check credentials file
            creds_file = self.config.claude_config_dir / ".credentials.json"
            info["credentials_file_exists"] = creds_file.exists()
            
            if not creds_file.exists():
                info["error"] = "No credentials file found"
                return info
            
            # Get authentication status
            try:
                result = self._run_claude_command(["auth", "whoami"], timeout=10)
                if result.returncode == 0:
                    output = result.stdout.strip()
                    
                    # Check for error patterns
                    error_patterns = ["Invalid API key", "Please run /login", "not authenticated"]
                    for pattern in error_patterns:
                        if pattern.lower() in output.lower():
                            info["error"] = f"Authentication error: {output}"
                            return info
                    
                    # Success
                    info["authenticated"] = True
                    info["user_info"] = output
                else:
                    info["error"] = f"Auth command failed: {result.stderr.strip()}"
                    
            except Exception as e:
                info["error"] = f"Error checking auth status: {e}"
            
            return info
            
        except Exception as e:
            raise ClaudeAuthError(
                f"Failed to get authentication info: {e}",
                error_code="AUTH_INFO_ERROR",
                suggestions=[
                    "Check Claude CLI installation",
                    "Verify Claude config directory permissions",
                    "Try running 'claude auth login'",
                ]
            )
    
    def create_session(
        self,
        user_id: Optional[Union[str, int]] = None,
        working_directory: Optional[Path] = None,
        session_id: Optional[str] = None,
        config_overrides: Optional[Dict[str, Any]] = None,
    ) -> SessionInfo:
        """Create a new Claude session.
        
        Args:
            user_id: User identifier for this session
            working_directory: Working directory for the session  
            session_id: Custom session ID (generated if None)
            config_overrides: Session-specific configuration overrides
            
        Returns:
            SessionInfo object for the new session
            
        Raises:
            ClaudeSessionError: If session creation fails
        """
        try:
            # Generate session ID if not provided
            if session_id is None:
                session_id = f"session_{int(time.time())}_{id(self)}"
            
            # Check if session already exists
            if session_id in self._sessions:
                raise ClaudeSessionError(
                    f"Session already exists: {session_id}",
                    session_id=session_id,
                    suggestions=["Use a different session ID", "Get existing session"]
                )
            
            # Create session info
            session = SessionInfo(
                session_id=session_id,
                user_id=user_id,
                working_directory=working_directory or self.config.working_directory,
                config=config_overrides or {},
            )
            
            # Store session
            self._sessions[session_id] = session
            self._save_sessions()
            
            logger.info(
                "Created new session",
                session_id=session_id,
                user_id=user_id,
                working_directory=str(session.working_directory)
            )
            
            return session
            
        except Exception as e:
            raise ClaudeSessionError(
                f"Failed to create session: {e}",
                session_id=session_id,
                suggestions=[
                    "Check session parameters",
                    "Ensure sufficient disk space",
                    "Verify permissions",
                ]
            )
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionInfo if session exists, None otherwise
        """
        session = self._sessions.get(session_id)
        
        if session:
            # Check if session is expired
            if session.is_expired(self.config.session_timeout_hours):
                logger.info("Session expired", session_id=session_id)
                session.status = SessionStatus.EXPIRED
                self._save_sessions()
        
        return session
    
    def update_session(
        self,
        session_id: str,
        cost: Optional[float] = None,
        turns: Optional[int] = None,
        tools_used: Optional[int] = None,
        status: Optional[SessionStatus] = None,
    ) -> bool:
        """Update session usage statistics.
        
        Args:
            session_id: Session to update
            cost: Cost to add to session total
            turns: Number of turns to add
            tools_used: Number of tools used to add
            status: New session status
            
        Returns:
            True if session was updated, False if session not found
        """
        session = self._sessions.get(session_id)
        if not session:
            logger.warning("Cannot update non-existent session", session_id=session_id)
            return False
        
        # Update usage statistics
        if cost is not None:
            session.total_cost += cost
        if turns is not None:
            session.total_turns += turns
        if tools_used is not None:
            session.total_tools_used += tools_used
        if status is not None:
            session.status = status
        
        # Update last used time
        session.last_used = time.time()
        
        # Check cost limits
        if session.total_cost > self.config.max_cost_per_session:
            logger.warning(
                "Session exceeded cost limit",
                session_id=session_id,
                total_cost=session.total_cost,
                limit=self.config.max_cost_per_session,
            )
            session.status = SessionStatus.FAILED
        
        # Save changes
        self._save_sessions()
        
        logger.debug(
            "Session updated",
            session_id=session_id,
            total_cost=session.total_cost,
            total_turns=session.total_turns,
            status=session.status.value,
        )
        
        return True
    
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
        sessions = []
        
        for session in self._sessions.values():
            # Filter by user if specified
            if user_id is not None and session.user_id != user_id:
                continue
            
            # Filter expired sessions if requested
            if not include_expired and session.is_expired(self.config.session_timeout_hours):
                continue
            
            sessions.append(session)
        
        # Sort by last used time (most recent first)
        sessions.sort(key=lambda s: s.last_used, reverse=True)
        return sessions
    
    def cleanup_expired_sessions(self) -> int:
        """Remove expired sessions.
        
        Returns:
            Number of sessions removed
        """
        expired_sessions = []
        
        for session_id, session in self._sessions.items():
            if session.is_expired(self.config.session_timeout_hours):
                expired_sessions.append(session_id)
        
        # Remove expired sessions
        for session_id in expired_sessions:
            del self._sessions[session_id]
        
        if expired_sessions:
            self._save_sessions()
            logger.info(
                "Cleaned up expired sessions",
                count=len(expired_sessions),
                session_ids=expired_sessions[:5]  # Log first 5 IDs
            )
        
        return len(expired_sessions)
    
    def get_usage_summary(
        self, user_id: Optional[Union[str, int]] = None
    ) -> Dict[str, Any]:
        """Get usage summary for user or all users.
        
        Args:
            user_id: User to get summary for (None for all users)
            
        Returns:
            Dictionary with usage statistics
        """
        sessions = self.list_sessions(user_id=user_id, include_expired=True)
        
        total_cost = sum(s.total_cost for s in sessions)
        total_turns = sum(s.total_turns for s in sessions)
        total_tools = sum(s.total_tools_used for s in sessions)
        
        active_sessions = [s for s in sessions if s.status == SessionStatus.ACTIVE]
        expired_sessions = [s for s in sessions if s.is_expired(self.config.session_timeout_hours)]
        
        return {
            "user_id": user_id,
            "total_sessions": len(sessions),
            "active_sessions": len(active_sessions),
            "expired_sessions": len(expired_sessions),
            "total_cost": total_cost,
            "total_turns": total_turns,
            "total_tools_used": total_tools,
            "avg_cost_per_session": total_cost / len(sessions) if sessions else 0.0,
            "last_activity": max((s.last_used for s in sessions), default=0),
        }
    
    def _run_claude_command(
        self, 
        args: List[str], 
        timeout: Optional[float] = None,
        cwd: Optional[Path] = None,
    ) -> subprocess.CompletedProcess:
        """Run Claude CLI command with error handling.
        
        Args:
            args: Command arguments
            timeout: Command timeout in seconds
            cwd: Working directory for command
            
        Returns:
            CompletedProcess result
            
        Raises:
            ClaudeAuthError: If command execution fails
        """
        try:
            # Find Claude CLI executable
            claude_path = self._find_claude_cli()
            if not claude_path:
                raise ClaudeAuthError(
                    "Claude CLI not found in PATH",
                    error_code="CLI_NOT_FOUND",
                    suggestions=[
                        "Install Claude CLI: npm install -g @anthropic-ai/claude-code",
                        "Add Claude CLI to PATH",
                        "Set CLAUDE_CLI_PATH environment variable",
                    ]
                )
            
            # Build command
            cmd = [claude_path] + args
            
            # Set up environment
            env = os.environ.copy()
            env.update(self.config.environment_vars)
            
            # Run command
            result = subprocess.run(
                cmd,
                cwd=str(cwd or self.config.working_directory),
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout or self.config.timeout_seconds,
            )
            
            logger.debug(
                "Claude command executed",
                cmd=cmd[:2],  # Don't log full command for security
                returncode=result.returncode,
                stdout_len=len(result.stdout),
                stderr_len=len(result.stderr),
            )
            
            return result
            
        except subprocess.TimeoutExpired as e:
            raise ClaudeAuthError(
                f"Claude command timed out after {e.timeout}s",
                error_code="CLI_TIMEOUT",
                details={"command": args, "timeout": e.timeout},
                suggestions=["Increase timeout", "Try simpler command", "Check system performance"]
            )
        except Exception as e:
            raise ClaudeAuthError(
                f"Failed to run Claude command: {e}",
                error_code="CLI_EXECUTION_ERROR",
                details={"command": args, "error": str(e)},
                suggestions=["Check Claude CLI installation", "Verify permissions", "Check system logs"]
            )
    
    def _find_claude_cli(self) -> Optional[str]:
        """Find Claude CLI executable.
        
        Returns:
            Path to Claude CLI executable, or None if not found
        """
        # Check configured path first
        if self.config.claude_cli_path:
            if Path(self.config.claude_cli_path).exists():
                return self.config.claude_cli_path
        
        # Check PATH
        claude_path = shutil.which("claude")
        if claude_path:
            return claude_path
        
        # Check common locations
        common_paths = [
            Path.home() / ".nvm/versions/node/*/bin/claude",
            Path.home() / ".npm-global/bin/claude", 
            Path("/usr/local/bin/claude"),
            Path("/usr/bin/claude"),
        ]
        
        for path_pattern in common_paths:
            if "*" in str(path_pattern):
                # Handle glob patterns
                import glob
                matches = glob.glob(str(path_pattern))
                if matches:
                    return matches[0]
            else:
                if path_pattern.exists():
                    return str(path_pattern)
        
        return None
    
    def _load_sessions(self) -> None:
        """Load sessions from disk."""
        try:
            if not self._session_file.exists():
                return
                
            with open(self._session_file, 'r') as f:
                data = json.load(f)
            
            # Convert dict data back to SessionInfo objects
            for session_id, session_data in data.items():
                try:
                    # Convert working_directory back to Path
                    if session_data.get("working_directory"):
                        session_data["working_directory"] = Path(session_data["working_directory"])
                    
                    # Convert status back to enum
                    if session_data.get("status"):
                        session_data["status"] = SessionStatus(session_data["status"])
                    
                    self._sessions[session_id] = SessionInfo(**session_data)
                    
                except Exception as e:
                    logger.warning(
                        "Failed to load session",
                        session_id=session_id,
                        error=str(e)
                    )
                    
            logger.info("Loaded sessions from disk", count=len(self._sessions))
            
        except Exception as e:
            logger.error("Failed to load sessions", error=str(e))
    
    def _save_sessions(self) -> None:
        """Save sessions to disk."""
        try:
            # Prepare data for JSON serialization
            data = {}
            for session_id, session in self._sessions.items():
                session_dict = {
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "working_directory": str(session.working_directory) if session.working_directory else None,
                    "created_at": session.created_at,
                    "last_used": session.last_used,
                    "total_cost": session.total_cost,
                    "total_turns": session.total_turns, 
                    "total_tools_used": session.total_tools_used,
                    "status": session.status.value,
                    "model_info": session.model_info,
                    "config": session.config,
                }
                data[session_id] = session_dict
            
            # Atomic write to prevent corruption
            temp_file = self._session_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            temp_file.replace(self._session_file)
            
            logger.debug("Saved sessions to disk", count=len(self._sessions))
            
        except Exception as e:
            logger.error("Failed to save sessions", error=str(e))