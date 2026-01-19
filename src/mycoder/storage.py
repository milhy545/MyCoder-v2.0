"""
Storage Manager for Next-Gen MyCoder.

Responsibility:
1. Persistent Storage (SQLite) for Chat History & Sessions
2. File Checkpointing (Snapshots) & Rollback Capability
3. Transactional Integrity for multi-file edits
"""

import sqlite3
import time
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ChatEntry:
    role: str
    content: str
    timestamp: float
    metadata: Dict[str, Any] = None
    session_id: str = "default"

class StorageManager:
    """
    Manages SQLite database for persistence and safety.
    """

    def __init__(self, working_dir: Optional[Path] = None, db_name: str = "session.db"):
        self.working_dir = working_dir or Path.cwd()
        self.db_path = self.working_dir / ".mycoder" / db_name
        self._ensure_db()

    def _ensure_db(self):
        """Initialize database schema."""
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Chat History Table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS chat_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        metadata TEXT
                    )
                """)

                # File Snapshots Table (for Undo/Rollback)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS file_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        step_id TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        content BLOB,
                        timestamp REAL NOT NULL
                    )
                """)

                # Indices
                conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_history(session_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_timestamp ON chat_history(timestamp)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_step ON file_snapshots(step_id)")

        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database at {self.db_path}: {e}")
            raise

    def save_interaction(self, session_id: str, role: str, content: str, metadata: Dict[str, Any] = None) -> int:
        """Saves a chat message."""
        try:
            meta_json = json.dumps(metadata) if metadata else "{}"
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "INSERT INTO chat_history (session_id, role, content, timestamp, metadata) VALUES (?, ?, ?, ?, ?)",
                    (session_id, role, content, time.time(), meta_json)
                )
                return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Failed to save interaction: {e}")
            return -1

    def get_history(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieves chat history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM chat_history WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
                    (session_id, limit)
                )
                rows = cursor.fetchall()

                history = []
                for row in rows:
                    history.append({
                        "role": row["role"],
                        "content": row["content"],
                        "timestamp": row["timestamp"],
                        "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
                    })
                return history
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve history: {e}")
            return []

    def create_snapshot(self, step_id: str, file_path: str) -> bool:
        """
        Saves the current content of a file before modification.
        Usage: Call this BEFORE writing to a file.
        """
        full_path = Path(file_path)
        if not full_path.is_absolute():
            full_path = self.working_dir / full_path

        if not full_path.exists():
            # If file doesn't exist, we store None as content (indicating it was created)
            content = None
        else:
            try:
                content = full_path.read_bytes()
            except OSError as e:
                logger.error(f"Failed to read file for snapshot {full_path}: {e}")
                return False

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO file_snapshots (step_id, file_path, content, timestamp) VALUES (?, ?, ?, ?)",
                    (step_id, str(full_path), content, time.time())
                )
            return True
        except sqlite3.Error as e:
            logger.error(f"Failed to save snapshot: {e}")
            return False

    def rollback(self, step_id: str) -> List[str]:
        """
        Restores all files modified in a specific step to their previous state.
        Returns list of restored file paths.
        """
        restored_files = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT file_path, content FROM file_snapshots WHERE step_id = ?",
                    (step_id,)
                )
                rows = cursor.fetchall()

                if not rows:
                    logger.warning(f"No snapshots found for step_id: {step_id}")
                    return []

                for file_path, content in rows:
                    path = Path(file_path)
                    try:
                        if content is None:
                            # File didn't exist before, so delete it
                            if path.exists():
                                path.unlink()
                        else:
                            # Restore content
                            path.parent.mkdir(parents=True, exist_ok=True)
                            path.write_bytes(content)
                        restored_files.append(file_path)
                    except OSError as e:
                        logger.error(f"Failed to restore file {file_path}: {e}")

                # Optional: Mark snapshots as used or keep them?
                # For now keep them, allowing multiple rollbacks if needed.

        except sqlite3.Error as e:
            logger.error(f"Rollback failed: {e}")

        return restored_files

    def cleanup_old_sessions(self, days: int = 30):
        """Removes history older than X days."""
        cutoff = time.time() - (days * 86400)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM chat_history WHERE timestamp < ?", (cutoff,))
                conn.execute("DELETE FROM file_snapshots WHERE timestamp < ?", (cutoff,))
                conn.execute("VACUUM")
        except sqlite3.Error as e:
            logger.error(f"Cleanup failed: {e}")
