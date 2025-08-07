"""Data models for Claude CLI authentication module.

This module contains all the data structures used throughout the library
for representing responses, updates, configurations, and other entities.
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class StreamType(Enum):
    """Types of streaming updates from Claude."""
    
    ASSISTANT = "assistant"
    USER = "user" 
    SYSTEM = "system"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    PROGRESS = "progress"
    RESULT = "result"


class SessionStatus(Enum):
    """Session status types."""
    
    ACTIVE = "active"
    EXPIRED = "expired"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class ClaudeResponse:
    """Response from Claude Code execution.
    
    Contains the complete response data from a Claude interaction,
    including content, metadata, cost information, and execution details.
    
    Attributes:
        content: The main response content from Claude
        session_id: Unique identifier for this conversation session
        cost: Cost in USD for this interaction
        duration_ms: Execution time in milliseconds
        num_turns: Number of conversation turns in this session
        is_error: Whether this response represents an error
        error_type: Type of error if is_error is True
        tools_used: List of tools that were executed during this interaction
        model_info: Information about the Claude model used
        created_at: Timestamp when response was created
    """
    
    content: str
    session_id: str
    cost: float = 0.0
    duration_ms: int = 0
    num_turns: int = 0
    is_error: bool = False
    error_type: Optional[str] = None
    tools_used: List[Dict[str, Any]] = field(default_factory=list)
    model_info: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)
    
    def is_successful(self) -> bool:
        """Check if response was successful (no errors)."""
        return not self.is_error
    
    def get_tool_names(self) -> List[str]:
        """Extract names of tools that were used."""
        return [tool.get("name", "unknown") for tool in self.tools_used]
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get a summary of execution metrics."""
        return {
            "duration_ms": self.duration_ms,
            "cost_usd": self.cost,
            "num_turns": self.num_turns,
            "tools_used": len(self.tools_used),
            "tool_names": self.get_tool_names(),
            "success": self.is_successful(),
        }


@dataclass
class StreamUpdate:
    """Streaming update from Claude Code execution.
    
    Represents a real-time update during Claude Code execution,
    allowing for progressive display of results and tool executions.
    
    Attributes:
        type: Type of update (assistant, user, system, etc.)
        content: Text content of this update
        tool_calls: List of tool calls in this update
        metadata: Additional metadata about the update
        timestamp: When this update occurred
        session_id: Session this update belongs to
        execution_id: Unique ID for this execution
        progress: Progress information if applicable
        error_info: Error details if this is an error update
    """
    
    type: Union[StreamType, str]
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: float = field(default_factory=time.time)
    session_id: Optional[str] = None
    execution_id: Optional[str] = field(default_factory=lambda: str(uuid.uuid4()))
    progress: Optional[Dict[str, Any]] = None
    error_info: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Convert string type to enum if needed."""
        if isinstance(self.type, str):
            try:
                self.type = StreamType(self.type)
            except ValueError:
                # Keep as string if not a known enum value
                pass
    
    def is_error(self) -> bool:
        """Check if this update represents an error."""
        return (
            self.type == StreamType.ERROR 
            or (self.metadata and self.metadata.get("is_error", False))
            or self.error_info is not None
        )
    
    def get_tool_names(self) -> List[str]:
        """Extract tool names from tool calls."""
        if not self.tool_calls:
            return []
        return [call.get("name", "unknown") for call in self.tool_calls if call.get("name")]
    
    def get_progress_percentage(self) -> Optional[int]:
        """Get progress percentage if available."""
        if self.progress:
            return self.progress.get("percentage")
        return None
    
    def get_error_message(self) -> Optional[str]:
        """Get error message if this is an error update."""
        if self.error_info:
            return self.error_info.get("message")
        elif self.is_error() and self.content:
            return self.content
        return None


@dataclass
class SessionInfo:
    """Information about a Claude session.
    
    Tracks metadata and state for a Claude conversation session,
    including usage statistics, timing, and configuration.
    
    Attributes:
        session_id: Unique identifier for the session
        user_id: User who owns this session (optional)
        working_directory: Working directory for this session
        created_at: When session was created
        last_used: When session was last accessed
        total_cost: Total cost accumulated in this session
        total_turns: Total number of conversation turns
        total_tools_used: Total number of tools executed
        status: Current status of the session
        model_info: Information about Claude model used
        config: Session-specific configuration
    """
    
    session_id: str
    user_id: Optional[Union[str, int]] = None
    working_directory: Optional[Path] = None
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    total_cost: float = 0.0
    total_turns: int = 0
    total_tools_used: int = 0
    status: SessionStatus = SessionStatus.ACTIVE
    model_info: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    
    def is_expired(self, timeout_hours: float = 24.0) -> bool:
        """Check if session is expired based on last use time."""
        if self.status != SessionStatus.ACTIVE:
            return True
            
        timeout_seconds = timeout_hours * 3600
        return (time.time() - self.last_used) > timeout_seconds
    
    def update_usage(self, response: ClaudeResponse) -> None:
        """Update session usage statistics from a response."""
        self.last_used = time.time()
        self.total_cost += response.cost
        self.total_turns += response.num_turns
        self.total_tools_used += len(response.tools_used)
        
        if response.is_error:
            self.status = SessionStatus.FAILED
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get summary of session usage."""
        age_minutes = (time.time() - self.created_at) / 60
        inactive_minutes = (time.time() - self.last_used) / 60
        
        return {
            "session_id": self.session_id,
            "age_minutes": age_minutes,
            "inactive_minutes": inactive_minutes, 
            "total_cost": self.total_cost,
            "total_turns": self.total_turns,
            "total_tools_used": self.total_tools_used,
            "status": self.status.value,
            "working_directory": str(self.working_directory) if self.working_directory else None,
        }


@dataclass
class AuthConfig:
    """Configuration for Claude CLI authentication.
    
    Contains all settings needed for Claude CLI authentication and execution,
    including paths, timeouts, security settings, and feature flags.
    
    Attributes:
        claude_cli_path: Path to Claude CLI executable
        claude_config_dir: Directory containing Claude CLI config
        timeout_seconds: Default timeout for Claude operations
        max_turns: Maximum conversation turns allowed
        allowed_tools: List of tools Claude is allowed to use
        use_sdk: Whether to use Python SDK as primary method
        enable_streaming: Whether to enable streaming responses
        session_timeout_hours: Hours before session expires
        max_cost_per_session: Maximum cost allowed per session
        working_directory: Default working directory
        environment_vars: Additional environment variables
    """
    
    claude_cli_path: Optional[str] = None
    claude_config_dir: Optional[Path] = None
    timeout_seconds: int = 120
    max_turns: int = 10
    allowed_tools: Optional[List[str]] = None
    use_sdk: bool = True
    enable_streaming: bool = True
    session_timeout_hours: float = 24.0
    max_cost_per_session: float = 1.0
    working_directory: Optional[Path] = None
    environment_vars: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and normalize configuration."""
        if self.claude_config_dir is None:
            self.claude_config_dir = Path.home() / ".claude"
            
        if self.working_directory is None:
            self.working_directory = Path.cwd()
            
        if self.allowed_tools is None:
            self.allowed_tools = [
                "Read", "Write", "Edit", "Bash", "Glob", "Grep", "LS", 
                "Task", "MultiEdit", "WebFetch", "TodoRead", "TodoWrite"
            ]
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check Claude CLI path
        if self.claude_cli_path and not Path(self.claude_cli_path).exists():
            issues.append(f"Claude CLI path does not exist: {self.claude_cli_path}")
            
        # Check config directory
        if not self.claude_config_dir.exists():
            issues.append(f"Claude config directory not found: {self.claude_config_dir}")
            
        # Check working directory
        if not self.working_directory.exists():
            issues.append(f"Working directory does not exist: {self.working_directory}")
            
        # Check timeout values
        if self.timeout_seconds <= 0:
            issues.append("timeout_seconds must be positive")
            
        if self.max_turns <= 0:
            issues.append("max_turns must be positive")
            
        if self.session_timeout_hours <= 0:
            issues.append("session_timeout_hours must be positive")
            
        return issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "claude_cli_path": self.claude_cli_path,
            "claude_config_dir": str(self.claude_config_dir),
            "timeout_seconds": self.timeout_seconds,
            "max_turns": self.max_turns,
            "allowed_tools": self.allowed_tools,
            "use_sdk": self.use_sdk,
            "enable_streaming": self.enable_streaming,
            "session_timeout_hours": self.session_timeout_hours,
            "max_cost_per_session": self.max_cost_per_session,
            "working_directory": str(self.working_directory),
            "environment_vars": self.environment_vars,
        }