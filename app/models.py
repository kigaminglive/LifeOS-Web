from datetime import datetime, date, timedelta
from app.database import get_connection


def create_task(title, category="Other", priority=3, estimated_minutes=30,
                energy_required=50, difficulty=3, deadline=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tasks
        (title, category, priority, estimated_minutes, energy_required, difficulty, deadline)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (title, category, priority, estimated_minutes, energy_required, difficulty, deadline or None))
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return task_id


def get_tasks(status=None):
    conn = get_connection()
    cur = conn.cursor()
    if status in ("pending", "completed"):
        cur.execute("SELECT * FROM tasks WHERE status=? ORDER BY id DESC", (status,))
    else:
        cur.execute("SELECT * FROM tasks ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_task(task_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_task(task_id, title, category, priority, estimated_minutes,
                energy_required, deadline=None, difficulty=3):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE tasks
        SET title=?, category=?, priority=?, estimated_minutes=?,
            energy_required=?, difficulty=?, deadline=?
        WHERE id=?
    """, (title, category, priority, estimated_minutes, energy_required, difficulty, deadline or None, task_id))
    conn.commit()
    conn.close()


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


def get_analytics():
    tasks = get_tasks()
    pending = [t for t in tasks if t["status"] == "pending"]
    completed = [t for t in tasks if t["status"] == "completed"]
    total = len(tasks)
    done = len(completed)
    rate = round((done / total) * 100, 1) if total else 0

    # category counts
    categories = {}
    for t in tasks:
        cat = t.get("category") or "Other"
        categories[cat] = categories.get(cat, 0) + 1

    # completed today
    today = date.today().isoformat()
    completed_today = 0
    for t in completed:
        ca = t.get("completed_at") or ""
        if ca.startswith(today):
            completed_today += 1

    # simple streak: consecutive days with at least 1 completion (from today backwards)
    days = set()
    for t in completed:
        ca = t.get("completed_at") or ""
        if len(ca) >= 10:
            days.add(ca[:10])

    streak = 0
    d = date.today()
    while d.isoformat() in days:
        streak += 1
        d -= timedelta(days=1)

    return {
        "total": total,
        "pending": len(pending),
        "completed": done,
        "rate": rate,
        "completed_today": completed_today,
        "categories": sorted(categories.items(), key=lambda x: x[1], reverse=True),
        "streak": streak,
        "history_count": len(get_decisions(1000)),
    }