"""
Storage Manager for Next-Gen MyCoder.

Responsibility:
1. Persistent Storage (SQLite) for Chat History & Sessions
2. File Checkpointing (Snapshots) & Rollback Capability
3. Asynchronous operations that are safe in async contexts
"""

import asyncio
import aiosqlite
import sqlite3
import time
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class StorageError(RuntimeError):
    """Raised when storage operations fail."""


@dataclass
class ChatEntry:
    role: str
    content: str
    timestamp: float
    metadata: Dict[str, Any] = None
    session_id: str = "default"


class StorageManager:
    """
    Manages SQLite database for persistence and safety using aiosqlite.
    Maintains a persistent connection to reduce overhead.
    """

    CREATE_CHAT_HISTORY = """
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp REAL NOT NULL,
            metadata TEXT
        )
    """
    CREATE_FILE_SNAPSHOTS = """
        CREATE TABLE IF NOT EXISTS file_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_id TEXT NOT NULL,
            file_path TEXT NOT NULL,
            content BLOB,
            timestamp REAL NOT NULL
        )
    """
    INDEX_CHATS = [
        "CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_chat_timestamp ON chat_history(timestamp)",
    ]
    INDEX_SNAPSHOTS = [
        "CREATE INDEX IF NOT EXISTS idx_snapshot_step ON file_snapshots(step_id)"
    ]

    def __init__(
        self,
        working_dir: Optional[Path] = None,
        db_name: str = "session.db",
        time_provider: Callable[[], float] = time.time,
    ):
        self.working_dir = working_dir or Path.cwd()
        self.db_path = self.working_dir / ".mycoder" / db_name
        self._lock = asyncio.Lock()
        self._initialized = False
        self._time_provider = time_provider
        self._conn: Optional[aiosqlite.Connection] = None

        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def connect(self):
        """Establishes the database connection if not already open."""
        async with self._lock:
            if self._conn is None:
                try:
                    self._conn = await aiosqlite.connect(self.db_path)
                    # Set row factory globally to avoid race conditions during concurrent access
                    self._conn.row_factory = aiosqlite.Row
                    await self._initialize_tables()
                except sqlite3.Error as e:
                    logger.error(
                        f"Failed to connect to database at {self.db_path}: {e}"
                    )
                    raise StorageError("Unable to connect to storage") from e

    async def close(self):
        """Closes the database connection."""
        async with self._lock:
            if self._conn:
                await self._conn.close()
                self._conn = None
                self._initialized = False

    async def _initialize_tables(self):
        """Initialize database schema."""
        if self._initialized:
            return

        try:
            await self._conn.execute(self.CREATE_CHAT_HISTORY)
            await self._conn.execute(self.CREATE_FILE_SNAPSHOTS)
            for index_stmt in self.INDEX_CHATS + self.INDEX_SNAPSHOTS:
                await self._conn.execute(index_stmt)
            await self._conn.commit()
            self._initialized = True
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database schema: {e}")
            raise StorageError("Unable to initialize storage schema") from e

    async def _ensure_conn(self):
        """Ensure connection is open and tables are initialized."""
        if self._conn is None:
            await self.connect()

    async def save_interaction(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Dict[str, Any] = None,
    ) -> int:
        """Saves a chat message asynchronously."""
        await self._ensure_conn()

        metadata_payload = "{}"
        if metadata:
            try:
                metadata_payload = json.dumps(metadata)
            except (TypeError, ValueError) as exc:
                logger.warning("Failed to serialize metadata: %s", exc)
                metadata_payload = "{}"

        try:
            await self._conn.execute(
                "INSERT INTO chat_history (session_id, role, content, timestamp, metadata) VALUES (?, ?, ?, ?, ?)",
                (
                    session_id,
                    role,
                    content,
                    self._time_provider(),
                    metadata_payload,
                ),
            )
            await self._conn.commit()
            cursor = await self._conn.execute("SELECT last_insert_rowid()")
            row = await cursor.fetchone()
            return row[0]
        except sqlite3.Error as e:
            logger.error(f"Failed to save interaction: {e}")
            raise StorageError("Failed to save interaction") from e

    async def get_history(
        self, session_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieves chat history asynchronously."""
        await self._ensure_conn()

        try:
            cursor = await self._conn.execute(
                "SELECT * FROM chat_history WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
                (session_id, limit),
            )
            rows = await cursor.fetchall()

            history = []
            for row in rows:
                metadata_content = {}
                if row["metadata"]:
                    try:
                        metadata_content = json.loads(row["metadata"])
                    except (TypeError, ValueError) as exc:
                        logger.warning("Corrupted metadata: %s", exc)
                history.append(
                    {
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": row["timestamp"],
                        "metadata": metadata_content,
                    }
                )
            return history
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve history: {e}")
            raise StorageError("Failed to fetch history") from e

    async def create_snapshot(self, step_id: str, file_path: str) -> bool:
        """
        Saves the current content of a file before modification.
        Usage: Call this BEFORE writing to a file.
        """
        await self._ensure_conn()

        full_path = Path(file_path)
        if not full_path.is_absolute():
            full_path = self.working_dir / full_path

        content = None
        if full_path.exists():
            try:
                content = await asyncio.to_thread(full_path.read_bytes)
            except OSError as e:
                logger.error(f"Failed to read file for snapshot {full_path}: {e}")
                raise StorageError("Unable to read file for snapshot") from e

        try:
            await self._conn.execute(
                "INSERT INTO file_snapshots (step_id, file_path, content, timestamp) VALUES (?, ?, ?, ?)",
                (step_id, str(full_path), content, self._time_provider()),
            )
            await self._conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to save snapshot: {e}")
            raise StorageError("Failed to save snapshot") from e

    async def rollback(self, step_id: str) -> List[str]:
        """
        Restores all files modified in a specific step to their previous state.
        Returns list of restored file paths.
        """
        await self._ensure_conn()

        restored_files: List[str] = []
        try:
            cursor = await self._conn.execute(
                "SELECT file_path, content FROM file_snapshots WHERE step_id = ?",
                (step_id,),
            )
            rows = await cursor.fetchall()

            if not rows:
                logger.warning(f"No snapshots found for step_id: {step_id}")
                return []

            for file_path, content in rows:
                path = Path(file_path)
                try:
                    if content is None:
                        if path.exists():
                            await asyncio.to_thread(path.unlink)
                    else:
                        await asyncio.to_thread(
                            path.parent.mkdir, parents=True, exist_ok=True
                        )
                        await asyncio.to_thread(path.write_bytes, content)
                    restored_files.append(file_path)
                except OSError as e:
                    logger.error(f"Failed to restore file {file_path}: {e}")
                    raise StorageError("Rollback failed during file restore") from e
        except sqlite3.Error as e:
            logger.error(f"Rollback failed: {e}")
            raise StorageError("Rollback query failed") from e

        return restored_files

    async def cleanup_old_sessions(self, days: int = 30):
        """Removes history older than X days."""
        await self._ensure_conn()

        cutoff = self._time_provider() - (days * 86400)
        try:
            await self._conn.execute(
                "DELETE FROM chat_history WHERE timestamp < ?", (cutoff,)
            )
            await self._conn.execute(
                "DELETE FROM file_snapshots WHERE timestamp < ?", (cutoff,)
            )
            await self._conn.commit()
            await self._conn.execute("VACUUM")
            await self._conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Cleanup failed: {e}")
            raise StorageError("Cleanup failed") from e
