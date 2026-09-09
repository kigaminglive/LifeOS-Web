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
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            category TEXT DEFAULT 'Other',
            priority INTEGER DEFAULT 3,
            estimated_minutes INTEGER DEFAULT 30,
            energy_required INTEGER DEFAULT 50,
            difficulty INTEGER DEFAULT 3,
            deadline TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_id INTEGER,
            task_title TEXT,
            score REAL,
            reason TEXT,
            mood TEXT,
            energy INTEGER,
            available_time TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()