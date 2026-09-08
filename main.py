from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database import init_db
from app.models import create_task, get_tasks, complete_task, delete_task
from app.decision import get_recommendation

app = FastAPI(title="LifeOS Web")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

init_db()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "tasks": get_tasks(),
            "pending_count": len(get_tasks("pending")),
            "completed_count": len(get_tasks("completed")),
            "recommendation": None,
        },
    )


@app.post("/tasks/add")
def add_task(
    title: str = Form(...),
    category: str = Form("Other"),
    priority: int = Form(3),
    estimated_minutes: int = Form(30),
    energy_required: int = Form(50),
):
    create_task(title, category, priority, estimated_minutes, energy_required)
    return RedirectResponse("/", status_code=303)


@app.post("/tasks/{task_id}/complete")
def mark_complete(task_id: int):
    complete_task(task_id)
    return RedirectResponse("/", status_code=303)


@app.post("/tasks/{task_id}/delete")
def remove_task(task_id: int):
    delete_task(task_id)
    return RedirectResponse("/", status_code=303)


@app.post("/decide", response_class=HTMLResponse)
def decide(
    request: Request,
    mood: str = Form("Neutral"),
    energy: int = Form(50),
    available_time: str = Form("30 min"),
):
    recommendation = get_recommendation(mood, energy, available_time)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "tasks": get_tasks(),
            "pending_count": len(get_tasks("pending")),
            "completed_count": len(get_tasks("completed")),
            "recommendation": recommendation,
            "mood": mood,
            "energy": energy,
            "available_time": available_time,
        },
    )