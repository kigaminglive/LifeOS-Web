from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import csv
import io

from app.database import init_db
from app.models import (
    create_task, get_tasks, get_task, update_task,
    complete_task, delete_task, get_decisions,
    clear_tasks, clear_history, get_analytics
)
from app.decision import get_recommendation

app = FastAPI(title="LifeOS")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
init_db()


def base_context(filter_status="all"):
    if filter_status in ("pending", "completed"):
        tasks = get_tasks(filter_status)
    else:
        tasks = get_tasks()
        filter_status = "all"

    return {
        "tasks": tasks,
        "filter_status": filter_status,
        "pending_count": len(get_tasks("pending")),
        "completed_count": len(get_tasks("completed")),
        "history": get_decisions(),
        "analytics": get_analytics(),
        "recommendation": None,
        "edit_task": None,
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request, tab: str = "home", filter: str = "all"):
    ctx = base_context(filter)
    ctx["request"] = request
    ctx["active"] = tab if tab in ("home", "tasks", "decide", "history", "settings") else "home"
    return templates.TemplateResponse(request=request, name="index.html", context=ctx)


@app.post("/tasks/add")
def add_task(
    title: str = Form(...),
    category: str = Form("Other"),
    priority: int = Form(3),
    estimated_minutes: int = Form(30),
    energy_required: int = Form(50),
    deadline: str = Form(""),
):
    create_task(title, category, priority, estimated_minutes, energy_required, deadline=deadline or None)
    return RedirectResponse("/?tab=tasks", status_code=303)


@app.get("/tasks/{task_id}/edit", response_class=HTMLResponse)
def edit_page(request: Request, task_id: int):
    task = get_task(task_id)
    if not task:
        return RedirectResponse("/?tab=tasks", status_code=303)
    ctx = base_context()
    ctx.update({"request": request, "active": "tasks", "edit_task": task})
    return templates.TemplateResponse(request=request, name="index.html", context=ctx)


@app.post("/tasks/{task_id}/edit")
def edit_save(
    task_id: int,
    title: str = Form(...),
    category: str = Form("Other"),
    priority: int = Form(3),
    estimated_minutes: int = Form(30),
    energy_required: int = Form(50),
    deadline: str = Form(""),
):
    update_task(task_id, title, category, priority, estimated_minutes, energy_required, deadline or None)
    return RedirectResponse("/?tab=tasks", status_code=303)


@app.post("/tasks/{task_id}/complete")
def mark_complete(task_id: int):
    complete_task(task_id)
    return RedirectResponse("/?tab=tasks", status_code=303)


@app.post("/tasks/{task_id}/delete")
def remove_task(task_id: int):
    delete_task(task_id)
    return RedirectResponse("/?tab=tasks", status_code=303)


@app.post("/decide", response_class=HTMLResponse)
def decide(
    request: Request,
    mood: str = Form("Neutral"),
    energy: int = Form(50),
    available_time: str = Form("30 min"),
):
    recommendation = get_recommendation(mood, energy, available_time)
    ctx = base_context()
    ctx.update({
        "request": request,
        "recommendation": recommendation,
        "mood": mood,
        "energy": energy,
        "available_time": available_time,
        "active": "decide",
    })
    return templates.TemplateResponse(request=request, name="index.html", context=ctx)


@app.post("/settings/clear-history")
def settings_clear_history():
    clear_history()
    return RedirectResponse("/?tab=settings", status_code=303)


@app.post("/settings/clear-tasks")
def settings_clear_tasks():
    clear_tasks()
    return RedirectResponse("/?tab=settings", status_code=303)


@app.get("/export.csv")
def export_csv():
    tasks = get_tasks()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "title", "category", "priority", "minutes", "energy", "deadline", "status", "created_at", "completed_at"])
    for t in tasks:
        writer.writerow([
            t.get("id"), t.get("title"), t.get("category"), t.get("priority"),
            t.get("estimated_minutes"), t.get("energy_required"), t.get("deadline"),
            t.get("status"), t.get("created_at"), t.get("completed_at"),
        ])
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=lifeos_tasks.csv"},
    )