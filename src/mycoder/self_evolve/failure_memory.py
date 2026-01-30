"""
Failure Memory (Reflexion Mechanism) for MyCoder v2.2.0.

Tracks tool execution failures, classifies them, and emits advisories to avoid
repeating known issues.
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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Generator, List, Optional

from .models import (
    Advisory,
    AdvisoryResult,
    ErrorType,
    EvolutionStatus,
    FailureRecord,
)

logger = logging.getLogger(__name__)


class FailureMemory:
    """Advisor that prevents repeating recent tool failures."""

    HARD_ERROR_TTL_DAYS = 7
    SOFT_ERROR_TTL_HOURS = 1

    WARN_THRESHOLD = 1
    BLOCK_THRESHOLD = 3

    def __init__(self, db_path: Optional[Path] = None) -> None:
        env_override = os.environ.get("MYCODER_LOCAL_MEMORY_DB")

        if db_path is None:
            if env_override:
                db_path = Path(env_override)
            else:
                db_path = Path.home() / ".mycoder" / "local_memory.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._init_database()

    def _init_database(self) -> None:
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
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Advisory API
    # ------------------------------------------------------------------

    def check_advisory(
        self,
        tool_name: str,
        params: Dict[str, Any],
        env_snapshot_hash: Optional[str] = None,
    ) -> Advisory:
        tool_signature = self._compute_tool_signature(tool_name, params)
        advisory_reason = "No previous failures recorded"
        records: List[FailureRecord] = []

        with self._lock:
            self._cleanup_expired()
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM failure_records
                    WHERE tool_signature = ?
                    ORDER BY updated_at DESC
                    """,
                    (tool_signature,),
                )
                rows = cursor.fetchall()

                if not rows:
                    return Advisory(result=AdvisoryResult.ALLOW, reason=advisory_reason)

                for row in rows:
                    record = FailureRecord.from_row(tuple(row))
                    if record.is_expired():
                        continue
                    if record.evolution_status == EvolutionStatus.RESOLVED:
                        continue

                    records.append(record)

                    if (
                        env_snapshot_hash
                        and record.env_snapshot_hash == env_snapshot_hash
                    ):
                        if record.retry_count >= self.BLOCK_THRESHOLD:
                            return Advisory(
                                result=AdvisoryResult.BLOCK,
                                reason=f"Blocked: {record.retry_count} recorded failures in this environment. "
                                f"Last error: {record.error_message}",
                                failure_record=record,
                                retry_count=record.retry_count,
                            )
                        if record.retry_count >= self.WARN_THRESHOLD:
                            return Advisory(
                                result=AdvisoryResult.WARN,
                                reason=f"Warning: {record.retry_count} failure(s) in this environment. "
                                f"Error: {record.error_message}",
                                failure_record=record,
                                retry_count=record.retry_count,
                            )

        if records and env_snapshot_hash:
            advisory_reason = (
                "Previous failures occurred in a different environment, allowing retry"
            )
        elif records:
            advisory_reason = "Previous failures exist but no matching environment hash"

        return Advisory(result=AdvisoryResult.ALLOW, reason=advisory_reason)

    def record_failure(
        self,
        tool_name: str,
        params: Dict[str, Any],
        error_message: str,
        env_snapshot_hash: str,
    ) -> None:
        tool_signature = self._compute_tool_signature(tool_name, params)
        error_type = self._classify_error(error_message)
        now = datetime.now(timezone.utc).isoformat()

        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM failure_records
                    WHERE tool_signature = ? AND env_snapshot_hash = ?
                    """,
                    (tool_signature, env_snapshot_hash),
                )
                record_row = cursor.fetchone()

                if record_row:
                    record = FailureRecord.from_row(tuple(record_row))
                    retry = record.retry_count + 1
                    conn.execute(
                        """
                        UPDATE failure_records
                        SET error_type = ?, retry_count = ?, updated_at = ?, error_message = ?, evolution_status = ?
                        WHERE id = ?
                        """,
                        (
                            error_type.value,
                            retry,
                            now,
                            error_message,
                            EvolutionStatus.PENDING.value,
                            record.id,
                        ),
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO failure_records (
                            tool_signature,
                            env_snapshot_hash,
                            error_type,
                            retry_count,
                            created_at,
                            updated_at,
                            error_message,
                            tool_name,
                            evolution_status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            tool_signature,
                            env_snapshot_hash,
                            error_type.value,
                            1,
                            now,
                            now,
                            error_message,
                            tool_name,
                            EvolutionStatus.PENDING.value,
                        ),
                    )
                conn.commit()

    def clear_failure(
        self,
        tool_name: str,
        params: Dict[str, Any],
        env_snapshot_hash: str,
    ) -> bool:
        tool_signature = self._compute_tool_signature(tool_name, params)
        now = datetime.now(timezone.utc).isoformat()

        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    SELECT * FROM failure_records
                    WHERE tool_signature = ? AND env_snapshot_hash = ?
                    """,
                    (tool_signature, env_snapshot_hash),
                )
                row = cursor.fetchone()
                if not row:
                    return False

                conn.execute(
                    """
                    UPDATE failure_records
                    SET evolution_status = ?, updated_at = ?
                    WHERE tool_signature = ? AND env_snapshot_hash = ?
                    """,
                    (
                        EvolutionStatus.RESOLVED.value,
                        now,
                        tool_signature,
                        env_snapshot_hash,
                    ),
                )
                conn.commit()
                return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_tool_signature(tool_name: str, params: Dict[str, Any]) -> str:
        normalized_params: Dict[str, Any] = {}
        for key in sorted(params.keys()):
            value = params[key]
            normalized_params[key] = value.strip() if isinstance(value, str) else value

        payload = {"tool": tool_name, "params": normalized_params}
        payload_str = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        return hashlib.sha256(payload_str.encode()).hexdigest()[:32]

    @staticmethod
    def compute_env_snapshot_hash(
        working_directory: Optional[Path] = None,
        file_context: Optional[List[str]] = None,
    ) -> str:
        components: List[str] = [
            str(working_directory or os.getcwd()),
            platform.system().lower(),
            f"{sys.version_info.major}.{sys.version_info.minor}",
        ]

        if file_context:
            components.append("|".join(sorted(file_context)))

        snapshot = "|".join(components)
        return hashlib.sha256(snapshot.encode()).hexdigest()[:32]

    @staticmethod
    def _classify_error(error_message: str) -> ErrorType:
        error_lower = error_message.lower()
        soft_patterns = [
            "connection",
            "timeout",
            "network",
            "permission denied",
            "disk",
            "space",
            "rate limit",
            "503",
            "502",
            "504",
            "temporary",
            "retry",
            "unavailable",
            "refused",
        ]

        for pattern in soft_patterns:
            if pattern in error_lower:
                return ErrorType.SOFT

        return ErrorType.HARD

    def _cleanup_expired(self) -> int:
        now = datetime.now(timezone.utc)
        hard_deadline = (now - timedelta(days=self.HARD_ERROR_TTL_DAYS)).isoformat()
        soft_deadline = (now - timedelta(hours=self.SOFT_ERROR_TTL_HOURS)).isoformat()

        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                DELETE FROM failure_records
                WHERE (error_type = 'HARD' AND updated_at < ?)
                   OR (error_type = 'SOFT' AND updated_at < ?)
                """,
                (hard_deadline, soft_deadline),
            )
            conn.commit()
            deleted = cursor.rowcount
            if deleted:
                logger.debug("FailureMemory expired %d records", deleted)

            return deleted

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
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
                "total": row[0] or 0,
                "hard_errors": row[1] or 0,
                "soft_errors": row[2] or 0,
                "pending": row[3] or 0,
                "resolved": row[4] or 0,
            }

    def get_recent_failures(self, limit: int = 10) -> List[FailureRecord]:
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM failure_records
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [FailureRecord.from_row(tuple(row)) for row in cursor.fetchall()]
