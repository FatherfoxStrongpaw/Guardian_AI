import sqlite3
import json
import time
from typing import Dict, Any, Optional
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.db_path = config["memory"]["path"]
        self._initialize_db()

    def _initialize_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    type TEXT,
                    timestamp REAL,
                    expires_at REAL NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS execution_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    directive_id TEXT,
                    status TEXT,
                    result TEXT,
                    timestamp REAL
                )
            """)

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def store(self, key: str, value: Any, type_hint: str = "general", ttl: Optional[int] = None):
        """Store a value with optional TTL"""
        serialized = json.dumps(value)
        timestamp = time.time()
        expires_at = timestamp + ttl if ttl else None

        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO memory (key, value, type, timestamp, expires_at) VALUES (?, ?, ?, ?, ?)",
                (key, serialized, type_hint, timestamp, expires_at)
            )
            logger.debug(f"Stored key: {key} of type: {type_hint}")

    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve a value, respecting TTL"""
        with self._get_connection() as conn:
            result = conn.execute(
                "SELECT value, expires_at FROM memory WHERE key = ?",
                (key,)
            ).fetchone()

            if not result:
                return None

            value, expires_at = result
            if expires_at and time.time() > expires_at:
                conn.execute("DELETE FROM memory WHERE key = ?", (key,))
                return None

            return json.loads(value)

    def log_execution(self, directive_id: str, status: str, result: Any):
        """Log execution history"""
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO execution_history (directive_id, status, result, timestamp) VALUES (?, ?, ?, ?)",
                (directive_id, status, json.dumps(result), time.time())
            )

    def get_execution_history(self, limit: int = 100) -> list:
        """Retrieve recent execution history"""
        with self._get_connection() as conn:
            results = conn.execute(
                "SELECT * FROM execution_history ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(zip(["id", "directive_id", "status", "result", "timestamp"], row)) for row in results]

    def cleanup(self):
        """Remove expired entries and old history"""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM memory WHERE expires_at < ?", (time.time(),))
            retention = time.time() - (self.config["memory"]["retention_days"] * 86400)
            conn.execute("DELETE FROM execution_history WHERE timestamp < ?", (retention,))