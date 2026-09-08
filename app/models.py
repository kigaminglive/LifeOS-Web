from datetime import datetime
from app.database import get_connection


def create_task(title, category="Other", priority=3, estimated_minutes=30,
                energy_required=50, difficulty=3, deadline=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tasks
        (title, category, priority, estimated_minutes, energy_required, difficulty, deadline)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (title, category, priority, estimated_minutes, energy_required, difficulty, deadline))
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return task_id


def get_tasks(status=None):
    conn = get_connection()
    cur = conn.cursor()
    if status:
        cur.execute("SELECT * FROM tasks WHERE status=? ORDER BY id DESC", (status,))
    else:
        cur.execute("SELECT * FROM tasks ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def complete_task(task_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE tasks SET status='completed', completed_at=? WHERE id=?",
        (datetime.now().isoformat(timespec="seconds"), task_id),
    )
    conn.commit()
    conn.close()


def delete_task(task_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()


def save_decision(task_id, task_title, score, reason, mood, energy, available_time):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO decisions
        (task_id, task_title, score, reason, mood, energy, available_time)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (task_id, task_title, score, reason, mood, energy, available_time))
    conn.commit()
    conn.close()


def get_decisions(limit=50):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def clear_tasks():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks")
    cur.execute("DELETE FROM decisions")
    conn.commit()
    conn.close()


def clear_history():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM decisions")
    conn.commit()
    conn.close()