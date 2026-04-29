import sqlite3
import os
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

class SemanticMemory:
    def __init__(self, db_path="data/memory.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        # Main memory table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Full-text search index
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                key, value, content='memories', content_rowid='id'
            )
        """)
        # Triggers to keep FTS in sync
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, key, value) VALUES (new.id, new.key, new.value);
            END
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, key, value) VALUES('delete', old.id, old.key, old.value);
            END
        """)
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, key, value) VALUES('delete', old.id, old.key, old.value);
                INSERT INTO memories_fts(rowid, key, value) VALUES (new.id, new.key, new.value);
            END
        """)
        self.conn.commit()
        logger.info("Memory database initialized.")

    def remember(self, key: str, value: str):
        """Store a memory (upsert)."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO memories (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
        """, (key.strip(), value.strip(), datetime.now().isoformat()))
        self.conn.commit()
        logger.debug(f"Stored: {key} = {value}")

    def recall(self, key: str) -> str | None:
        """Exact key lookup."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM memories WHERE key=?", (key.strip(),))
        row = cursor.fetchone()
        return row['value'] if row else None

    def search(self, query: str, limit=5) -> list:
        """Full-text search across keys and values."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT key, value FROM memories_fts
            WHERE memories_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query.strip(), limit))
        rows = cursor.fetchall()
        return [(row['key'], row['value']) for row in rows]

    def forget(self, key: str):
        """Delete a memory by key."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM memories WHERE key=?", (key.strip(),))
        self.conn.commit()
        logger.debug(f"Forgot: {key}")

    def all_keys(self) -> list:
        """List all stored memory keys."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT key FROM memories ORDER BY updated_at DESC")
        return [row['key'] for row in cursor.fetchall()]
