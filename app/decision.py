from app.models import get_tasks, save_decision


def parse_minutes(time_str: str) -> int:
    return {
        "15 min": 15,
        "30 min": 30,
        "45 min": 45,
        "1 hour": 60,
        "2+ hours": 120,
    }.get(time_str, 30)


def score_task(task, energy: int, available_minutes: int):
    reasons = []
    score = 0.0

    priority = int(task.get("priority", 3))
    score += (priority / 5 * 100) * 0.30
    reasons.append(f"Priority {priority}/5")

    est = int(task.get("estimated_minutes", 30))
    if est <= available_minutes:
        time_score = 100
        reasons.append("Fits available time")
    elif est <= available_minutes * 1.5:
        time_score = 60
        reasons.append("Slightly over available time")
    else:
        time_score = 25
        reasons.append("Needs more time than available")
    score += time_score * 0.25

    need = int(task.get("energy_required", 50))
    diff = abs(need - energy)
    energy_score = max(0, 100 - diff)
    score += energy_score * 0.25
    reasons.append("Energy match is good" if diff <= 20 else "Energy match is average")

    difficulty = int(task.get("difficulty", 3))
    if energy >= 70:
        diff_score = 100 - (difficulty - 1) * 10
    elif energy <= 35:
        diff_score = max(0, 100 - difficulty * 15)
    else:
        diff_score = 70
    score += diff_score * 0.20

    return round(score, 1), reasons


def get_recommendation(mood: str, energy: int, available_time: str):
    tasks = get_tasks(status="pending")
    if not tasks:
        return None

    available_minutes = parse_minutes(available_time)
    ranked = []
    for task in tasks:
        s, reasons = score_task(task, int(energy), available_minutes)
        ranked.append((s, task, reasons))

    ranked.sort(key=lambda x: x[0], reverse=True)
    best_score, best_task, best_reasons = ranked[0]

    save_decision(
        task_id=best_task["id"],
        task_title=best_task["title"],
        score=best_score,
        reason=" | ".join(best_reasons),
        mood=mood,
        energy=int(energy),
        available_time=available_time,
    )

    return {
        "task": best_task,
        "score": best_score,
        "reasons": best_reasons,
        "mood": mood,
    }