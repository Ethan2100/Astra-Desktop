import sqlite3
from pathlib import Path
from core.config import DATABASE_PATH

class Database:
    """Small SQLite layer. The database lives outside the source folder."""

    def __init__(self, path: Path = DATABASE_PATH):
        self.path = Path(path)

    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self):
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    assistant_id TEXT NOT NULL DEFAULT 'astra',
                    title TEXT NOT NULL DEFAULT 'New conversation',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(conversation_id) REFERENCES conversations(id)
                        ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    assistant_id TEXT NOT NULL DEFAULT 'astra',
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_messages_conversation
                    ON chat_messages(conversation_id);
                CREATE INDEX IF NOT EXISTS idx_memories_assistant
                    ON memories(assistant_id);
            """)

    def create_conversation(self, assistant_id="astra", title="New conversation"):
        with self.connect() as db:
            cursor = db.execute(
                "INSERT INTO conversations (assistant_id, title) VALUES (?, ?)",
                (assistant_id, title),
            )
            return cursor.lastrowid

    def add_message(self, conversation_id, role, content):
        if role not in {"user", "assistant", "system"}:
            raise ValueError("role must be user, assistant, or system")
        with self.connect() as db:
            db.execute(
                "INSERT INTO chat_messages (conversation_id, role, content) VALUES (?, ?, ?)",
                (conversation_id, role, content),
            )
            db.execute(
                "UPDATE conversations SET updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (conversation_id,),
            )

    def list_conversations(self, assistant_id="astra"):
        with self.connect() as db:
            rows = db.execute(
                """SELECT id, title, created_at, updated_at
                   FROM conversations WHERE assistant_id=?
                   ORDER BY updated_at DESC""",
                (assistant_id,),
            ).fetchall()
            return [dict(row) for row in rows]

    def list_memories(self, assistant_id="astra"):
        with self.connect() as db:
            rows = db.execute(
                """SELECT id, content, created_at, updated_at FROM memories
                   WHERE assistant_id=? ORDER BY updated_at DESC""",
                (assistant_id,),
            ).fetchall()
            return [dict(row) for row in rows]
