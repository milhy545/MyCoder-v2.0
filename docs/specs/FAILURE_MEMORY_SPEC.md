# Failure Memory (Reflexion Mechanism) - Implementation Spec

## Overview

**Module:** `src/mycoder/self_evolve/failure_memory.py`
**Storage:** SQLite (`~/.mycoder/local_memory.db`)
**Purpose:** Prevent the AI agent from repeating the same mistakes (anti-loop mechanism)

This document provides a step-by-step implementation guide for a Junior Developer to implement the "Failure Memory" feature using the Advisor Pattern.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Tool Registry                                  │
│                      (tool_registry.py)                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   execute_tool(tool_name, context, **kwargs)                            │
│         │                                                                │
│         ▼                                                                │
│   ┌─────────────────────────────────────────┐                           │
│   │  1. CHECK ADVISORY (FailureMemory)      │                           │
│   │     - compute tool_signature            │                           │
│   │     - compute env_snapshot_hash         │                           │
│   │     - lookup in SQLite                  │                           │
│   │     - apply TTL rules                   │                           │
│   │     - return ALLOW / WARN / BLOCK       │                           │
│   └─────────────────────────────────────────┘                           │
│         │                                                                │
│         ▼                                                                │
│   ┌─────────────────────────────────────────┐                           │
│   │  2. EXECUTE TOOL                        │                           │
│   │     (if advisory allows)                │                           │
│   └─────────────────────────────────────────┘                           │
│         │                                                                │
│         ▼                                                                │
│   ┌─────────────────────────────────────────┐                           │
│   │  3. RECORD FAILURE (if failed)          │                           │
│   │     - store tool_signature              │                           │
│   │     - store env_snapshot_hash           │                           │
│   │     - classify error_type (HARD/SOFT)   │                           │
│   │     - increment retry_count             │                           │
│   └─────────────────────────────────────────┘                           │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
src/mycoder/self_evolve/
├── __init__.py           # UPDATE: export FailureMemory
├── failure_memory.py     # NEW: Main FailureMemory class
├── models.py             # UPDATE: add FailureRecord dataclass
├── manager.py            # existing
├── storage.py            # existing
└── ...

~/.mycoder/
└── local_memory.db       # NEW: SQLite database (auto-created)
```

---

## SQLite Schema

```sql
-- File: Schema for ~/.mycoder/local_memory.db

CREATE TABLE IF NOT EXISTS failure_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Unique signature identifying the tool + params combination
    tool_signature TEXT NOT NULL,

    -- Hash of environment state (CWD, OS, file context)
    env_snapshot_hash TEXT NOT NULL,

    -- Error classification: 'HARD' (syntax/logic) or 'SOFT' (network/disk)
    error_type TEXT NOT NULL CHECK (error_type IN ('HARD', 'SOFT')),

    -- Number of times this exact failure has been retried
    retry_count INTEGER NOT NULL DEFAULT 1,

    -- When the failure was first recorded
    created_at TEXT NOT NULL,

    -- When the failure was last encountered
    updated_at TEXT NOT NULL,

    -- Error message for debugging
    error_message TEXT,

    -- Tool name for easy filtering
    tool_name TEXT NOT NULL,

    -- Evolution status: 'PENDING', 'RESOLVED', 'IGNORED'
    evolution_status TEXT NOT NULL DEFAULT 'PENDING',

    -- Unique constraint to prevent duplicates
    UNIQUE(tool_signature, env_snapshot_hash)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_failure_lookup
    ON failure_records(tool_signature, env_snapshot_hash);

-- Index for TTL cleanup queries
CREATE INDEX IF NOT EXISTS idx_failure_ttl
    ON failure_records(error_type, updated_at);

-- Index for tool-based queries
CREATE INDEX IF NOT EXISTS idx_failure_tool
    ON failure_records(tool_name);
```

---

## Data Models

### New Dataclass: `FailureRecord`

Add to `src/mycoder/self_evolve/models.py`:

```python
from enum import Enum

class ErrorType(Enum):
    """Error classification for TTL rules."""
    HARD = "HARD"   # Syntax/logic errors - 7 day TTL
    SOFT = "SOFT"   # Network/disk errors - 1 hour TTL

class EvolutionStatus(Enum):
    """Status of failure resolution."""
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"

class AdvisoryResult(Enum):
    """Result of check_advisory() call."""
    ALLOW = "ALLOW"     # Proceed with execution
    WARN = "WARN"       # Proceed but notify LLM of previous failure
    BLOCK = "BLOCK"     # Block execution, require justification

@dataclass
class FailureRecord:
    """Stored failure record from SQLite."""
    id: int
    tool_signature: str
    env_snapshot_hash: str
    error_type: ErrorType
    retry_count: int
    created_at: str
    updated_at: str
    error_message: Optional[str]
    tool_name: str
    evolution_status: EvolutionStatus

    def is_expired(self) -> bool:
        """Check if this failure record has expired based on TTL rules."""
        from datetime import datetime, timedelta

        updated = datetime.fromisoformat(self.updated_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)

        if self.error_type == ErrorType.HARD:
            ttl = timedelta(days=7)
        else:  # SOFT
            ttl = timedelta(hours=1)

        return (now - updated) > ttl

@dataclass
class Advisory:
    """Advisory result returned by check_advisory()."""
    result: AdvisoryResult
    reason: str
    failure_record: Optional[FailureRecord] = None
    retry_count: int = 0
```

---

## Pseudo-code: Hashing Logic

### Tool Signature Hash

```python
def compute_tool_signature(tool_name: str, params: Dict[str, Any]) -> str:
    """
    Create a deterministic hash of tool + parameters.

    Strategy:
    1. Sort parameters by key (deterministic ordering)
    2. Normalize values (strip whitespace, lowercase paths on Windows)
    3. Create JSON string
    4. SHA256 hash

    Example:
        tool_name = "file_write"
        params = {"path": "src/main.py", "content": "print('hello')"}

        normalized = {
            "tool": "file_write",
            "params": {"content": "print('hello')", "path": "src/main.py"}
        }

        signature = sha256(json.dumps(normalized, sort_keys=True))
    """
    import hashlib
    import json

    # Normalize parameters
    normalized_params = {}
    for key, value in sorted(params.items()):
        if isinstance(value, str):
            # Normalize paths and strip whitespace
            normalized_params[key] = value.strip()
        else:
            normalized_params[key] = value

    payload = {
        "tool": tool_name,
        "params": normalized_params
    }

    json_str = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(json_str.encode()).hexdigest()[:32]  # First 32 chars
```

### Environment Snapshot Hash

```python
def compute_env_snapshot_hash(context: ToolExecutionContext) -> str:
    """
    Create a hash representing the current environment state.

    This is CRITICAL for the Advisor pattern:
    - Same tool+params in DIFFERENT environment = ALLOW retry
    - Same tool+params in SAME environment = BLOCK/WARN

    Strategy (cheap but effective):
    1. CWD (current working directory)
    2. OS platform (linux/darwin/win32)
    3. Python version (major.minor)
    4. Optional: Hash of relevant file mtimes in context

    Example:
        cwd = "/home/user/project"
        os = "linux"
        python = "3.11"

        snapshot = sha256(f"{cwd}|{os}|{python}")
    """
    import hashlib
    import platform
    import sys
    import os

    components = [
        # Working directory
        str(context.working_directory or os.getcwd()),

        # OS platform
        platform.system().lower(),

        # Python version
        f"{sys.version_info.major}.{sys.version_info.minor}",
    ]

    # Optional: Add file context if available
    if context.metadata and "file_context" in context.metadata:
        files = context.metadata["file_context"]
        if isinstance(files, list):
            # Add sorted file paths for determinism
            components.append("|".join(sorted(files)))

    snapshot_str = "|".join(components)
    return hashlib.sha256(snapshot_str.encode()).hexdigest()[:32]
```

### Error Classification

```python
def classify_error(error: str) -> ErrorType:
    """
    Classify error as HARD (logic/syntax) or SOFT (transient).

    HARD errors (7-day TTL):
    - SyntaxError, TypeError, ValueError
    - ImportError, ModuleNotFoundError
    - AttributeError, NameError
    - Logic errors (assertion failures)

    SOFT errors (1-hour TTL):
    - ConnectionError, TimeoutError
    - FileNotFoundError, PermissionError
    - OSError (disk full, etc.)
    - HTTP errors (5xx, rate limits)
    """
    error_lower = error.lower()

    SOFT_PATTERNS = [
        "connection", "timeout", "network",
        "permission denied", "disk", "space",
        "rate limit", "503", "502", "504",
        "temporary", "retry", "unavailable"
    ]

    for pattern in SOFT_PATTERNS:
        if pattern in error_lower:
            return ErrorType.SOFT

    # Default to HARD for logic/syntax errors
    return ErrorType.HARD
```

---

## FailureMemory Class

### Complete Implementation Skeleton

```python
"""
Failure Memory (Reflexion Mechanism) for MyCoder v2.2.0

Prevents the AI agent from repeating the same mistakes by tracking
tool execution failures and providing advisory decisions.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import sqlite3
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Generator, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Data Classes
# ============================================================================

class ErrorType(Enum):
    HARD = "HARD"
    SOFT = "SOFT"

class EvolutionStatus(Enum):
    PENDING = "PENDING"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"

class AdvisoryResult(Enum):
    ALLOW = "ALLOW"
    WARN = "WARN"
    BLOCK = "BLOCK"


@dataclass
class FailureRecord:
    """Stored failure record from SQLite."""
    id: int
    tool_signature: str
    env_snapshot_hash: str
    error_type: ErrorType
    retry_count: int
    created_at: str
    updated_at: str
    error_message: Optional[str]
    tool_name: str
    evolution_status: EvolutionStatus

    def is_expired(self) -> bool:
        updated = datetime.fromisoformat(self.updated_at.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        ttl = timedelta(days=7) if self.error_type == ErrorType.HARD else timedelta(hours=1)
        return (now - updated) > ttl

    @staticmethod
    def from_row(row: tuple) -> "FailureRecord":
        return FailureRecord(
            id=row[0],
            tool_signature=row[1],
            env_snapshot_hash=row[2],
            error_type=ErrorType(row[3]),
            retry_count=row[4],
            created_at=row[5],
            updated_at=row[6],
            error_message=row[7],
            tool_name=row[8],
            evolution_status=EvolutionStatus(row[9]),
        )


@dataclass
class Advisory:
    """Advisory result returned by check_advisory()."""
    result: AdvisoryResult
    reason: str
    failure_record: Optional[FailureRecord] = None
    retry_count: int = 0


# ============================================================================
# Main FailureMemory Class
# ============================================================================

class FailureMemory:
    """
    Tracks tool execution failures to prevent repetitive mistakes.

    Uses the Advisor Pattern:
    - check_advisory(): Query before tool execution
    - record_failure(): Store after tool failure
    - clear_failure(): Remove when issue is resolved
    """

    # TTL configuration
    HARD_ERROR_TTL_DAYS = 7
    SOFT_ERROR_TTL_HOURS = 1

    # Advisory thresholds
    WARN_THRESHOLD = 1   # Warn after 1 retry
    BLOCK_THRESHOLD = 3  # Block after 3 retries

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize FailureMemory with SQLite storage.

        Args:
            db_path: Path to SQLite database. Defaults to ~/.mycoder/local_memory.db
        """
        if db_path is None:
            db_path = Path.home() / ".mycoder" / "local_memory.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._init_database()

    def _init_database(self) -> None:
        """Initialize SQLite database with schema."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS failure_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_signature TEXT NOT NULL,
                    env_snapshot_hash TEXT NOT NULL,
                    error_type TEXT NOT NULL CHECK (error_type IN ('HARD', 'SOFT')),
                    retry_count INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error_message TEXT,
                    tool_name TEXT NOT NULL,
                    evolution_status TEXT NOT NULL DEFAULT 'PENDING',
                    UNIQUE(tool_signature, env_snapshot_hash)
                );

                CREATE INDEX IF NOT EXISTS idx_failure_lookup
                    ON failure_records(tool_signature, env_snapshot_hash);
                CREATE INDEX IF NOT EXISTS idx_failure_ttl
                    ON failure_records(error_type, updated_at);
                CREATE INDEX IF NOT EXISTS idx_failure_tool
                    ON failure_records(tool_name);
            """)
            conn.commit()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Get thread-safe database connection."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # ========================================================================
    # Public API: Advisory Pattern
    # ========================================================================

    def check_advisory(
        self,
        tool_name: str,
        params: Dict[str, Any],
        env_snapshot_hash: Optional[str] = None,
    ) -> Advisory:
        """
        Check if a tool execution should proceed.

        Advisor Rules:
        1. If error exists AND env_snapshot_hash matches → BLOCK/WARN
        2. If error exists BUT env_snapshot_hash differs → ALLOW
        3. If error is expired (TTL) → ALLOW

        Args:
            tool_name: Name of the tool
            params: Tool parameters
            env_snapshot_hash: Pre-computed env hash (optional)

        Returns:
            Advisory with result (ALLOW/WARN/BLOCK) and reason
        """
        tool_sig = self._compute_tool_signature(tool_name, params)

        with self._lock:
            # First, cleanup expired records
            self._cleanup_expired()

            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM failure_records
                    WHERE tool_signature = ?
                    ORDER BY updated_at DESC
                    """,
                    (tool_sig,)
                )
                rows = cursor.fetchall()

                if not rows:
                    return Advisory(
                        result=AdvisoryResult.ALLOW,
                        reason="No previous failures recorded"
                    )

                # Check for same environment failures
                for row in rows:
                    record = FailureRecord.from_row(tuple(row))

                    # Skip expired records
                    if record.is_expired():
                        continue

                    # Skip resolved records
                    if record.evolution_status == EvolutionStatus.RESOLVED:
                        continue

                    # Check environment match
                    if env_snapshot_hash and record.env_snapshot_hash == env_snapshot_hash:
                        # Same environment - apply blocking rules
                        if record.retry_count >= self.BLOCK_THRESHOLD:
                            return Advisory(
                                result=AdvisoryResult.BLOCK,
                                reason=f"Blocked: {record.retry_count} failures in same environment. "
                                       f"Error: {record.error_message}",
                                failure_record=record,
                                retry_count=record.retry_count
                            )
                        elif record.retry_count >= self.WARN_THRESHOLD:
                            return Advisory(
                                result=AdvisoryResult.WARN,
                                reason=f"Warning: {record.retry_count} previous failure(s). "
                                       f"Error: {record.error_message}",
                                failure_record=record,
                                retry_count=record.retry_count
                            )

                # Different environment - allow retry
                return Advisory(
                    result=AdvisoryResult.ALLOW,
                    reason="Environment changed since last failure, retry allowed"
                )

    def record_failure(
        self,
        tool_name: str,
        params: Dict[str, Any],
        error_message: str,
        env_snapshot_hash: str,
    ) -> FailureRecord:
        """
        Record a tool execution failure.

        Args:
            tool_name: Name of the tool
            params: Tool parameters
            error_message: The error message
            env_snapshot_hash: Hash of current environment

        Returns:
            The created or updated FailureRecord
        """
        tool_sig = self._compute_tool_signature(tool_name, params)
        error_type = self._classify_error(error_message)
        now = datetime.now(timezone.utc).isoformat()

        with self._lock:
            with self._get_connection() as conn:
                # Try to update existing record
                cursor = conn.execute(
                    """
                    UPDATE failure_records
                    SET retry_count = retry_count + 1,
                        updated_at = ?,
                        error_message = ?,
                        error_type = ?
                    WHERE tool_signature = ? AND env_snapshot_hash = ?
                    RETURNING *
                    """,
                    (now, error_message, error_type.value, tool_sig, env_snapshot_hash)
                )
                row = cursor.fetchone()

                if row:
                    conn.commit()
                    return FailureRecord.from_row(tuple(row))

                # Insert new record
                cursor = conn.execute(
                    """
                    INSERT INTO failure_records
                    (tool_signature, env_snapshot_hash, error_type, retry_count,
                     created_at, updated_at, error_message, tool_name, evolution_status)
                    VALUES (?, ?, ?, 1, ?, ?, ?, ?, 'PENDING')
                    RETURNING *
                    """,
                    (tool_sig, env_snapshot_hash, error_type.value, now, now,
                     error_message, tool_name)
                )
                row = cursor.fetchone()
                conn.commit()

                logger.info(f"Recorded failure for {tool_name}: {error_message[:50]}...")
                return FailureRecord.from_row(tuple(row))

    def clear_failure(
        self,
        tool_name: str,
        params: Dict[str, Any],
        env_snapshot_hash: Optional[str] = None,
    ) -> bool:
        """
        Mark a failure as resolved (e.g., after successful retry).

        Args:
            tool_name: Name of the tool
            params: Tool parameters
            env_snapshot_hash: Optional specific environment to clear

        Returns:
            True if a record was updated
        """
        tool_sig = self._compute_tool_signature(tool_name, params)
        now = datetime.now(timezone.utc).isoformat()

        with self._lock:
            with self._get_connection() as conn:
                if env_snapshot_hash:
                    cursor = conn.execute(
                        """
                        UPDATE failure_records
                        SET evolution_status = 'RESOLVED', updated_at = ?
                        WHERE tool_signature = ? AND env_snapshot_hash = ?
                        """,
                        (now, tool_sig, env_snapshot_hash)
                    )
                else:
                    cursor = conn.execute(
                        """
                        UPDATE failure_records
                        SET evolution_status = 'RESOLVED', updated_at = ?
                        WHERE tool_signature = ?
                        """,
                        (now, tool_sig)
                    )
                conn.commit()
                return cursor.rowcount > 0

    # ========================================================================
    # Environment Hashing
    # ========================================================================

    @staticmethod
    def compute_env_snapshot_hash(
        working_directory: Optional[Path] = None,
        file_context: Optional[list] = None,
    ) -> str:
        """
        Compute hash of current environment state.

        Args:
            working_directory: Current working directory
            file_context: Optional list of relevant file paths

        Returns:
            32-character hex hash
        """
        components = [
            str(working_directory or os.getcwd()),
            platform.system().lower(),
            f"{sys.version_info.major}.{sys.version_info.minor}",
        ]

        if file_context:
            components.append("|".join(sorted(str(f) for f in file_context)))

        snapshot_str = "|".join(components)
        return hashlib.sha256(snapshot_str.encode()).hexdigest()[:32]

    # ========================================================================
    # Internal Methods
    # ========================================================================

    @staticmethod
    def _compute_tool_signature(tool_name: str, params: Dict[str, Any]) -> str:
        """Compute deterministic hash of tool + parameters."""
        normalized_params = {}
        for key, value in sorted(params.items()):
            if isinstance(value, str):
                normalized_params[key] = value.strip()
            else:
                normalized_params[key] = value

        payload = {"tool": tool_name, "params": normalized_params}
        json_str = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:32]

    @staticmethod
    def _classify_error(error: str) -> ErrorType:
        """Classify error as HARD (logic) or SOFT (transient)."""
        error_lower = error.lower()

        soft_patterns = [
            "connection", "timeout", "network", "permission denied",
            "disk", "space", "rate limit", "503", "502", "504",
            "temporary", "retry", "unavailable", "refused"
        ]

        for pattern in soft_patterns:
            if pattern in error_lower:
                return ErrorType.SOFT

        return ErrorType.HARD

    def _cleanup_expired(self) -> int:
        """Remove expired records based on TTL rules."""
        now = datetime.now(timezone.utc)
        hard_cutoff = (now - timedelta(days=self.HARD_ERROR_TTL_DAYS)).isoformat()
        soft_cutoff = (now - timedelta(hours=self.SOFT_ERROR_TTL_HOURS)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                DELETE FROM failure_records
                WHERE (error_type = 'HARD' AND updated_at < ?)
                   OR (error_type = 'SOFT' AND updated_at < ?)
                """,
                (hard_cutoff, soft_cutoff)
            )
            conn.commit()
            deleted = cursor.rowcount

            if deleted > 0:
                logger.debug(f"Cleaned up {deleted} expired failure records")

            return deleted

    # ========================================================================
    # Statistics and Debugging
    # ========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get failure memory statistics."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN error_type = 'HARD' THEN 1 ELSE 0 END) as hard_errors,
                    SUM(CASE WHEN error_type = 'SOFT' THEN 1 ELSE 0 END) as soft_errors,
                    SUM(CASE WHEN evolution_status = 'PENDING' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN evolution_status = 'RESOLVED' THEN 1 ELSE 0 END) as resolved
                FROM failure_records
            """)
            row = cursor.fetchone()

            return {
                "total_records": row[0] or 0,
                "hard_errors": row[1] or 0,
                "soft_errors": row[2] or 0,
                "pending": row[3] or 0,
                "resolved": row[4] or 0,
            }

    def get_recent_failures(self, limit: int = 10) -> list:
        """Get most recent failure records."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM failure_records
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,)
            )
            return [FailureRecord.from_row(tuple(row)) for row in cursor.fetchall()]
```

---

## Integration with Tool Registry

### Modify `src/mycoder/tool_registry.py`

```python
# Add import at top of file
from .self_evolve.failure_memory import FailureMemory, Advisory, AdvisoryResult

# In ToolRegistry class __init__:
def __init__(self):
    self.tools: Dict[str, BaseTool] = {}
    self.categories: Dict[ToolCategory, List[str]] = {}
    self.event_handlers: Dict[str, List[Callable]] = {}
    self.failure_memory = FailureMemory()  # NEW: Add failure memory
    self._initialize_core_tools()

# Modify execute_tool method:
async def execute_tool(
    self, tool_name: str, context: ToolExecutionContext, **kwargs
) -> ToolResult:
    """Execute a tool with validation, advisory check, and monitoring."""

    if tool_name not in self.tools:
        return ToolResult(
            success=False,
            data=None,
            tool_name=tool_name,
            duration_ms=0,
            error=f"Tool {tool_name} not found",
        )

    tool = self.tools[tool_name]

    # ====================================================================
    # NEW: Check Failure Memory Advisory
    # ====================================================================
    env_hash = FailureMemory.compute_env_snapshot_hash(
        working_directory=context.working_directory,
        file_context=context.metadata.get("file_context") if context.metadata else None
    )

    advisory = self.failure_memory.check_advisory(
        tool_name=tool_name,
        params=kwargs,
        env_snapshot_hash=env_hash
    )

    if advisory.result == AdvisoryResult.BLOCK:
        logger.warning(f"Tool execution blocked by Failure Memory: {advisory.reason}")
        return ToolResult(
            success=False,
            data=None,
            tool_name=tool_name,
            duration_ms=0,
            error=f"BLOCKED by Failure Memory: {advisory.reason}",
            metadata={"advisory": advisory.result.value, "retry_count": advisory.retry_count}
        )

    if advisory.result == AdvisoryResult.WARN:
        logger.warning(f"Tool execution warning from Failure Memory: {advisory.reason}")
        # Emit warning event for LLM to see
        self._emit_event("failure_memory_warning", {
            "tool_name": tool_name,
            "advisory": advisory,
            "context": context
        })
    # ====================================================================

    # Check if tool can execute in current mode
    if not tool.can_execute_in_mode(context.mode):
        return ToolResult(
            success=False,
            data=None,
            tool_name=tool_name,
            duration_ms=0,
            error=f"Tool {tool_name} not available in {context.mode} mode",
        )

    # Validate context
    try:
        if not await tool.validate_context(context):
            return ToolResult(
                success=False,
                data=None,
                tool_name=tool_name,
                duration_ms=0,
                error=f"Context validation failed for {tool_name}",
            )
    except Exception as e:
        return ToolResult(
            success=False,
            data=None,
            tool_name=tool_name,
            duration_ms=0,
            error=f"Context validation error: {e}",
        )

    # Emit pre-execution event
    self._emit_event(
        "tool_pre_execution", {"tool_name": tool_name, "context": context}
    )

    # Execute tool
    try:
        result = await tool.execute(context, **kwargs)

        # ================================================================
        # NEW: Record failure or clear on success
        # ================================================================
        if not result.success:
            self.failure_memory.record_failure(
                tool_name=tool_name,
                params=kwargs,
                error_message=result.error or "Unknown error",
                env_snapshot_hash=env_hash
            )
        else:
            # Clear any previous failure for this tool+params
            self.failure_memory.clear_failure(
                tool_name=tool_name,
                params=kwargs,
                env_snapshot_hash=env_hash
            )
        # ================================================================

        # Emit post-execution event
        self._emit_event(
            "tool_post_execution",
            {"tool_name": tool_name, "result": result, "context": context},
        )

        return result

    except Exception as e:
        logger.error(f"Tool execution failed: {tool_name} - {e}")

        # ================================================================
        # NEW: Record failure on exception
        # ================================================================
        self.failure_memory.record_failure(
            tool_name=tool_name,
            params=kwargs,
            error_message=str(e),
            env_snapshot_hash=env_hash
        )
        # ================================================================

        error_result = ToolResult(
            success=False,
            data=None,
            tool_name=tool_name,
            duration_ms=0,
            error=f"Execution error: {e}",
        )

        self._emit_event(
            "tool_execution_error",
            {"tool_name": tool_name, "error": error_result, "context": context},
        )

        return error_result
```

---

## Implementation Steps (ToDo List for Codex)

### Phase 1: Data Models (30 min)

1. **Open** `src/mycoder/self_evolve/models.py`
2. **Add imports**: `from enum import Enum` at top
3. **Add** `ErrorType` enum class after existing imports
4. **Add** `EvolutionStatus` enum class
5. **Add** `AdvisoryResult` enum class
6. **Add** `FailureRecord` dataclass with `from_row()` static method
7. **Add** `Advisory` dataclass
8. **Run** linter: `poetry run black src/mycoder/self_evolve/models.py`

### Phase 2: FailureMemory Class (60 min)

9. **Create** new file: `src/mycoder/self_evolve/failure_memory.py`
10. **Add** file header docstring and imports
11. **Implement** `FailureMemory.__init__()` with db_path handling
12. **Implement** `_init_database()` with SQLite schema
13. **Implement** `_get_connection()` context manager
14. **Implement** `_compute_tool_signature()` static method
15. **Implement** `compute_env_snapshot_hash()` static method
16. **Implement** `_classify_error()` static method
17. **Implement** `check_advisory()` method with all rules
18. **Implement** `record_failure()` method with upsert logic
19. **Implement** `clear_failure()` method
20. **Implement** `_cleanup_expired()` method
21. **Implement** `get_stats()` and `get_recent_failures()` methods
22. **Run** formatter: `poetry run black src/mycoder/self_evolve/failure_memory.py`

### Phase 3: Module Exports (10 min)

23. **Open** `src/mycoder/self_evolve/__init__.py`
24. **Add** import: `from .failure_memory import FailureMemory, Advisory, AdvisoryResult`
25. **Update** `__all__` list to include new exports

### Phase 4: Tool Registry Integration (45 min)

26. **Open** `src/mycoder/tool_registry.py`
27. **Add** import at top: `from .self_evolve.failure_memory import ...`
28. **Modify** `ToolRegistry.__init__()` to create `self.failure_memory`
29. **Modify** `execute_tool()` - add advisory check BEFORE mode check
30. **Modify** `execute_tool()` - add failure recording AFTER execution
31. **Modify** `execute_tool()` - add success clearing in result handling
32. **Run** formatter: `poetry run black src/mycoder/tool_registry.py`

### Phase 5: Unit Tests (45 min)

33. **Create** `tests/unit/test_failure_memory.py`
34. **Write** test: `test_compute_tool_signature_deterministic`
35. **Write** test: `test_compute_env_snapshot_hash`
36. **Write** test: `test_classify_error_hard_vs_soft`
37. **Write** test: `test_record_failure_creates_record`
38. **Write** test: `test_record_failure_increments_retry_count`
39. **Write** test: `test_check_advisory_allow_first_time`
40. **Write** test: `test_check_advisory_warn_after_threshold`
41. **Write** test: `test_check_advisory_block_after_threshold`
42. **Write** test: `test_check_advisory_allow_different_env`
43. **Write** test: `test_ttl_expiration_hard_errors`
44. **Write** test: `test_ttl_expiration_soft_errors`
45. **Write** test: `test_clear_failure_marks_resolved`
46. **Run** tests: `poetry run pytest tests/unit/test_failure_memory.py -v`

### Phase 6: Integration Tests (30 min)

47. **Create** `tests/integration/test_failure_memory_integration.py`
48. **Write** test: `test_tool_registry_blocks_repeated_failures`
49. **Write** test: `test_tool_registry_allows_different_env`
50. **Write** test: `test_tool_registry_clears_on_success`
51. **Run** tests: `poetry run pytest tests/integration/test_failure_memory_integration.py -v`

### Phase 7: Final Verification (15 min)

52. **Run** full linter: `poetry run black . && poetry run isort .`
53. **Run** type checker: `poetry run mypy src/mycoder/self_evolve/failure_memory.py`
54. **Run** full test suite: `poetry run pytest tests/unit/ tests/integration/ -v`
55. **Update** `AGENTS.md` with implementation notes

---

## Test File Template

```python
"""Unit tests for FailureMemory (Reflexion Mechanism)."""

import tempfile
from pathlib import Path

import pytest

from mycoder.self_evolve.failure_memory import (
    Advisory,
    AdvisoryResult,
    ErrorType,
    FailureMemory,
    FailureRecord,
)


@pytest.fixture
def failure_memory(tmp_path):
    """Create FailureMemory with temporary database."""
    db_path = tmp_path / "test_memory.db"
    return FailureMemory(db_path=db_path)


class TestToolSignature:
    """Tests for tool signature computation."""

    def test_deterministic_same_params(self, failure_memory):
        sig1 = failure_memory._compute_tool_signature("file_read", {"path": "test.py"})
        sig2 = failure_memory._compute_tool_signature("file_read", {"path": "test.py"})
        assert sig1 == sig2

    def test_different_params_different_signature(self, failure_memory):
        sig1 = failure_memory._compute_tool_signature("file_read", {"path": "a.py"})
        sig2 = failure_memory._compute_tool_signature("file_read", {"path": "b.py"})
        assert sig1 != sig2

    def test_param_order_independent(self, failure_memory):
        sig1 = failure_memory._compute_tool_signature("tool", {"a": 1, "b": 2})
        sig2 = failure_memory._compute_tool_signature("tool", {"b": 2, "a": 1})
        assert sig1 == sig2


class TestErrorClassification:
    """Tests for error type classification."""

    def test_connection_error_is_soft(self, failure_memory):
        assert failure_memory._classify_error("Connection refused") == ErrorType.SOFT

    def test_timeout_error_is_soft(self, failure_memory):
        assert failure_memory._classify_error("Request timeout") == ErrorType.SOFT

    def test_syntax_error_is_hard(self, failure_memory):
        assert failure_memory._classify_error("SyntaxError: invalid") == ErrorType.HARD

    def test_type_error_is_hard(self, failure_memory):
        assert failure_memory._classify_error("TypeError: cannot") == ErrorType.HARD


class TestAdvisoryPattern:
    """Tests for the Advisor pattern."""

    def test_allow_first_execution(self, failure_memory):
        advisory = failure_memory.check_advisory("file_read", {"path": "test.py"})
        assert advisory.result == AdvisoryResult.ALLOW

    def test_warn_after_first_failure(self, failure_memory):
        env_hash = FailureMemory.compute_env_snapshot_hash()

        # Record a failure
        failure_memory.record_failure(
            tool_name="file_read",
            params={"path": "test.py"},
            error_message="File not found",
            env_snapshot_hash=env_hash
        )

        # Check advisory
        advisory = failure_memory.check_advisory(
            "file_read", {"path": "test.py"}, env_snapshot_hash=env_hash
        )
        assert advisory.result == AdvisoryResult.WARN

    def test_block_after_multiple_failures(self, failure_memory):
        env_hash = FailureMemory.compute_env_snapshot_hash()

        # Record multiple failures
        for _ in range(3):
            failure_memory.record_failure(
                tool_name="file_read",
                params={"path": "test.py"},
                error_message="File not found",
                env_snapshot_hash=env_hash
            )

        # Check advisory
        advisory = failure_memory.check_advisory(
            "file_read", {"path": "test.py"}, env_snapshot_hash=env_hash
        )
        assert advisory.result == AdvisoryResult.BLOCK

    def test_allow_different_environment(self, failure_memory):
        env_hash_1 = "environment_1_hash_abc123"
        env_hash_2 = "environment_2_hash_xyz789"

        # Record failure in env 1
        for _ in range(3):
            failure_memory.record_failure(
                tool_name="file_read",
                params={"path": "test.py"},
                error_message="File not found",
                env_snapshot_hash=env_hash_1
            )

        # Check advisory in env 2 - should ALLOW
        advisory = failure_memory.check_advisory(
            "file_read", {"path": "test.py"}, env_snapshot_hash=env_hash_2
        )
        assert advisory.result == AdvisoryResult.ALLOW


class TestClearFailure:
    """Tests for clearing/resolving failures."""

    def test_clear_marks_resolved(self, failure_memory):
        env_hash = FailureMemory.compute_env_snapshot_hash()

        # Record and then clear
        failure_memory.record_failure(
            tool_name="file_read",
            params={"path": "test.py"},
            error_message="Error",
            env_snapshot_hash=env_hash
        )

        result = failure_memory.clear_failure(
            tool_name="file_read",
            params={"path": "test.py"},
            env_snapshot_hash=env_hash
        )

        assert result is True

        # Advisory should now ALLOW
        advisory = failure_memory.check_advisory(
            "file_read", {"path": "test.py"}, env_snapshot_hash=env_hash
        )
        assert advisory.result == AdvisoryResult.ALLOW
```

---

## Acceptance Criteria

1. **SQLite database** auto-creates at `~/.mycoder/local_memory.db`
2. **Tool signature hash** is deterministic (same inputs = same hash)
3. **Environment hash** includes CWD, OS, Python version
4. **Error classification** correctly identifies HARD vs SOFT errors
5. **Advisory ALLOW** on first execution of any tool
6. **Advisory WARN** after 1-2 failures in same environment
7. **Advisory BLOCK** after 3+ failures in same environment
8. **Advisory ALLOW** when environment changes (different hash)
9. **TTL expiration**: HARD errors expire after 7 days, SOFT after 1 hour
10. **Clear on success**: Tool success clears previous failure records
11. **Thread-safe**: Concurrent access handled with locking
12. **All tests pass**: `poetry run pytest tests/unit/test_failure_memory.py -v`

---

## Notes for Codex

- Follow existing code style in `src/mycoder/self_evolve/` (see `storage.py`, `models.py`)
- Use `from __future__ import annotations` for forward references
- Keep SQLite queries simple - no ORM needed
- Use `threading.Lock` for thread safety (not asyncio.Lock)
- Test with `tmp_path` fixture for isolated database per test
- Run `poetry run black` and `poetry run isort` after each file change
