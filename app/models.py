from datetime import datetime, date, timedelta
from app.database import get_connection


def create_task(user_id, title, category="Other", priority=3, estimated_minutes=30,
                energy_required=50, difficulty=3, deadline=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tasks
        (user_id, title, category, priority, estimated_minutes, energy_required, difficulty, deadline)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, title, category, priority, estimated_minutes,
        energy_required, difficulty, deadline or None
    ))
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return task_id


def get_tasks(user_id, status=None):
    conn = get_connection()
    cur = conn.cursor()
    if status in ("pending", "completed"):
        cur.execute(
            "SELECT * FROM tasks WHERE user_id=? AND status=? ORDER BY id DESC",
            (user_id, status),
        )
    else:
        cur.execute(
            "SELECT * FROM tasks WHERE user_id=? ORDER BY id DESC",
            (user_id,),
        )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_task(user_id, task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM tasks WHERE id=? AND user_id=?",
        (task_id, user_id),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_task(user_id, task_id, title, category, priority, estimated_minutes,
                energy_required, deadline=None, difficulty=3):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE tasks
        SET title=?, category=?, priority=?, estimated_minutes=?,
            energy_required=?, difficulty=?, deadline=?
        WHERE id=? AND user_id=?
    """, (
        title, category, priority, estimated_minutes, energy_required,
        difficulty, deadline or None, task_id, user_id
    ))
    conn.commit()
    conn.close()


def complete_task(user_id, task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE tasks
        SET status='completed', completed_at=?
        WHERE id=? AND user_id=?
        """,
        (datetime.now().isoformat(timespec="seconds"), task_id, user_id),
    )
    conn.commit()
    conn.close()


def delete_task(user_id, task_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (task_id, user_id))
    conn.commit()
    conn.close()


def save_decision(user_id, task_id, task_title, score, reason, mood, energy, available_time):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO decisions
        (user_id, task_id, task_title, score, reason, mood, energy, available_time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, task_id, task_title, score, reason, mood, energy, available_time))
    conn.commit()
    conn.close()


def get_decisions(user_id, limit=50):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM decisions WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def clear_tasks(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE user_id=?", (user_id,))
    cur.execute("DELETE FROM decisions WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def clear_history(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM decisions WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def get_analytics(user_id):
    tasks = get_tasks(user_id)
    pending = [t for t in tasks if t["status"] == "pending"]
    completed = [t for t in tasks if t["status"] == "completed"]
    total = len(tasks)
    done = len(completed)
    rate = round((done / total) * 100, 1) if total else 0.0

    categories = {}
    for t in tasks:
        cat = t.get("category") or "Other"
        categories[cat] = categories.get(cat, 0) + 1

    today = date.today().isoformat()
    completed_today = 0
    for t in completed:
        ca = t.get("completed_at") or ""
        if ca.startswith(today):
            completed_today += 1

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
        "history_count": len(get_decisions(user_id, 1000)),
    }