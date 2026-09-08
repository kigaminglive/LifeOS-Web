import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "lifeos_web.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT DEFAULT 'Other',
            priority INTEGER DEFAULT 3,
            estimated_minutes INTEGER DEFAULT 30,
            energy_required INTEGER DEFAULT 50,
            difficulty INTEGER DEFAULT 3,
            deadline TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT
        )
    """)
    conn.commit()
    conn.close()