import sqlite3
import time
import logging
from pathlib import Path
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "mycoder_memory.db"):
        self.db_path = Path(db_path)
        self.timeout = 20.0
        self._init_db()

    def _init_db(self):
        query = """
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE,
            value TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.execute_with_retry(query)

    def execute_with_retry(self, query: str, params: tuple = (), max_retries: int = 5) -> List[Any]:
        delay = 1.0
        last_error = None
        for attempt in range(max_retries):
            try:
                with sqlite3.connect(self.db_path, timeout=self.timeout) as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.fetchall()
            except sqlite3.OperationalError as e:
                last_error = e
                if "database is locked" in str(e).lower() or "timeout" in str(e).lower():
                    logger.warning(f"[DB Retry {attempt+1}/{max_retries}] DB locked/timeout. Waiting {delay}s...")
                    time.sleep(delay)
                    delay *= 2
                else:
                    raise e
        logger.error(f"Critical DB failure after {max_retries} attempts: {last_error}")
        raise last_error

    def get(self, key: str) -> Optional[str]:
        result = self.execute_with_retry("SELECT value FROM memory WHERE key = ?", (key,))
        return result[0][0] if result else None

    def set(self, key: str, value: str):
        self.execute_with_retry(
            "INSERT OR REPLACE INTO memory (key, value) VALUES (?, ?)",
            (key, value)
        )
