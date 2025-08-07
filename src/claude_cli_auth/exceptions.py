"""Custom exceptions for Claude CLI authentication module.

This module defines all custom exceptions used throughout the library,
providing clear error hierarchies and detailed error information for
different failure scenarios.
"""

from typing import Any, Dict, List, Optional


class ClaudeAuthError(Exception):
    """Base exception for all Claude authentication errors.
    
    This is the root exception class that all other exceptions inherit from.
    It provides common functionality for error handling and reporting.
    
    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code
        details: Additional error details and context
        suggestions: List of suggested solutions
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.suggestions = suggestions or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "suggestions": self.suggestions,
        }
    
    def get_user_message(self) -> str:
        """Get user-friendly error message with suggestions."""
        msg = [self.message]
        
        if self.suggestions:
            msg.append("\nSuggestions:")
            for suggestion in self.suggestions:
                msg.append(f"• {suggestion}")
        
        return "\n".join(msg)


class ClaudeAuthManagerError(ClaudeAuthError):
    """Errors related to the main ClaudeAuthManager."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None
    ):
        if not suggestions:
            suggestions = [
                "Check Claude CLI installation with 'claude --version'",
                "Verify authentication with 'claude auth whoami'",
                "Review configuration settings",
                "Check debug logs for more details",
            ]
        super().__init__(message, error_code, details, suggestions)


class ClaudeCLIError(ClaudeAuthError):
    """Errors related to Claude CLI execution."""
    
    def __init__(
        self,
        message: str,
        exit_code: Optional[int] = None,
        stderr: Optional[str] = None,
        command: Optional[List[str]] = None,
        suggestions: Optional[List[str]] = None
    ):
        details = {
            "exit_code": exit_code,
            "stderr": stderr,
            "command": command,
        }
        
        if not suggestions:
            suggestions = []
            
            if exit_code == 1:
                suggestions.append("Check Claude CLI authentication status")
            elif exit_code == 127:
                suggestions.append("Install Claude CLI: npm install -g @anthropic-ai/claude-code")
            elif "permission" in (stderr or "").lower():
                suggestions.append("Check file and directory permissions")
            elif "timeout" in (stderr or "").lower():
                suggestions.append("Increase timeout value or try smaller requests")
            else:
                suggestions.extend([
                    "Check Claude CLI installation",
                    "Verify working directory exists",
                    "Try running the command manually",
                ])
        
        super().__init__(message, "CLI_ERROR", details, suggestions)
    
    @property
    def exit_code(self) -> Optional[int]:
        """Get exit code from command execution."""
        return self.details.get("exit_code")
    
    @property
    def stderr(self) -> Optional[str]:
        """Get stderr output from command execution."""
        return self.details.get("stderr")
    
    @property
    def command(self) -> Optional[List[str]]:
        """Get the command that was executed."""
        return self.details.get("command")


class ClaudeTimeoutError(ClaudeAuthError):
    """Error when Claude operations timeout."""
    
    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        details = {
            "timeout_seconds": timeout_seconds,
            "operation": operation,
        }
        
        if not suggestions:
            suggestions = [
                "Increase timeout value in configuration",
                "Break down request into smaller parts",
                "Check network connectivity",
                "Try again with simpler request",
            ]
        
        super().__init__(message, "TIMEOUT_ERROR", details, suggestions)


class ClaudeSessionError(ClaudeAuthError):
    """Errors related to session management."""
    
    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        session_status: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        details = {
            "session_id": session_id,
            "session_status": session_status,
        }
        
        if not suggestions:
            suggestions = [
                "Create a new session",
                "Check if session has expired",
                "Verify session ID is correct",
                "Clear expired sessions",
            ]
        
        super().__init__(message, "SESSION_ERROR", details, suggestions)
    
    @property 
    def session_id(self) -> Optional[str]:
        """Get the session ID associated with this error."""
        return self.details.get("session_id")


class ClaudeConfigError(ClaudeAuthError):
    """Errors related to configuration and setup."""
    
    def __init__(
        self,
        message: str,
        config_field: Optional[str] = None,
        config_value: Optional[Any] = None,
        suggestions: Optional[List[str]] = None
    ):
        details = {
            "config_field": config_field,
            "config_value": config_value,
        }
        
        if not suggestions:
            suggestions = []
            
            if config_field == "claude_cli_path":
                suggestions.extend([
                    "Install Claude CLI: npm install -g @anthropic-ai/claude-code",
                    "Add Claude CLI to PATH",
                    "Set CLAUDE_CLI_PATH environment variable",
                ])
            elif config_field == "claude_config_dir":
                suggestions.extend([
                    "Run 'claude auth login' to create configuration",
                    "Check ~/.claude directory permissions",
                ])
            elif config_field == "working_directory":
                suggestions.extend([
                    "Create the working directory",
                    "Check directory permissions",
                    "Use absolute path",
                ])
            else:
                suggestions.extend([
                    "Check configuration values",
                    "Review documentation for valid options",
                    "Use default configuration as starting point",
                ])
        
        super().__init__(message, "CONFIG_ERROR", details, suggestions)


class ClaudeParsingError(ClaudeAuthError):
    """Errors related to parsing Claude responses."""
    
    def __init__(
        self,
        message: str,
        raw_data: Optional[str] = None,
        parse_stage: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        details = {
            "raw_data": raw_data[:500] if raw_data else None,  # Truncate for safety
            "parse_stage": parse_stage,
        }
        
        if not suggestions:
            suggestions = [
                "Try the request again",
                "Use smaller or simpler prompts",
                "Check Claude CLI version compatibility",
                "Report issue if problem persists",
            ]
        
        super().__init__(message, "PARSING_ERROR", details, suggestions)


class ClaudeToolValidationError(ClaudeAuthError):
    """Errors related to tool validation and security."""
    
    def __init__(
        self,
        message: str,
        blocked_tools: Optional[List[str]] = None,
        allowed_tools: Optional[List[str]] = None,
        validation_rule: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        details = {
            "blocked_tools": blocked_tools or [],
            "allowed_tools": allowed_tools or [],
            "validation_rule": validation_rule,
        }
        
        if not suggestions:
            suggestions = []
            
            if blocked_tools:
                suggestions.append(f"Add {', '.join(blocked_tools)} to allowed_tools configuration")
            
            suggestions.extend([
                "Contact administrator to modify tool permissions",
                "Use alternative approaches that don't require blocked tools",
                "Check current allowed tools with get_config()",
            ])
        
        super().__init__(message, "TOOL_VALIDATION_ERROR", details, suggestions)
    
    @property
    def blocked_tools(self) -> List[str]:
        """Get list of tools that were blocked."""
        return self.details.get("blocked_tools", [])
    
    @property
    def allowed_tools(self) -> List[str]:
        """Get list of currently allowed tools."""
        return self.details.get("allowed_tools", [])


class ClaudeRateLimitError(ClaudeAuthError):
    """Errors related to rate limiting."""
    
    def __init__(
        self,
        message: str,
        reset_time: Optional[str] = None,
        limit_type: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        details = {
            "reset_time": reset_time,
            "limit_type": limit_type,
        }
        
        if not suggestions:
            suggestions = [
                f"Wait until {reset_time} for limit to reset" if reset_time else "Wait for rate limit to reset",
                "Use smaller requests to conserve quota",
                "Implement request queuing with delays",
                "Contact support if you need higher limits",
            ]
        
        super().__init__(message, "RATE_LIMIT_ERROR", details, suggestions)


class ClaudeNetworkError(ClaudeAuthError):
    """Errors related to network connectivity."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        url: Optional[str] = None,
        suggestions: Optional[List[str]] = None
    ):
        details = {
            "status_code": status_code,
            "url": url,
        }
        
        if not suggestions:
            suggestions = [
                "Check internet connectivity",
                "Verify Claude service status",
                "Try again in a few moments",
                "Check firewall and proxy settings",
            ]
        
        super().__init__(message, "NETWORK_ERROR", details, suggestions)