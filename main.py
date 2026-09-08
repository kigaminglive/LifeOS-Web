from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import init_db
from app.models import (
    create_task, get_tasks, complete_task, delete_task,
    get_decisions, clear_tasks, clear_history
)
from app.decision import get_recommendation

app = FastAPI(title="LifeOS")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

init_db()


def base_context():
    return {
        "tasks": get_tasks(),
        "pending_count": len(get_tasks("pending")),
        "completed_count": len(get_tasks("completed")),
        "history": get_decisions(),
        "recommendation": None,
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    ctx = base_context()
    ctx["request"] = request
    ctx["active"] = "tasks"
    return templates.TemplateResponse(request=request, name="index.html", context=ctx)


@app.post("/tasks/add")
def add_task(
    title: str = Form(...),
    category: str = Form("Other"),
    priority: int = Form(3),
    estimated_minutes: int = Form(30),
    energy_required: int = Form(50),
):
    create_task(title, category, priority, estimated_minutes, energy_required)
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