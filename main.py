from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import csv
import io

from app.database import init_db
from app.auth import (
    create_user, authenticate, set_session, clear_session, get_current_user
)
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


def require_user(request: Request):
    return get_current_user(request)


def base_context(user, filter_status="all"):
    uid = user["id"]
    if filter_status in ("pending", "completed"):
        tasks = get_tasks(uid, filter_status)
    else:
        tasks = get_tasks(uid)
        filter_status = "all"

    return {
        "user": user,
        "tasks": tasks,
        "filter_status": filter_status,
        "pending_count": len(get_tasks(uid, "pending")),
        "completed_count": len(get_tasks(uid, "completed")),
        "history": get_decisions(uid),
        "analytics": get_analytics(uid),
        "recommendation": None,
        "edit_task": None,
    }


# ---------- AUTH PAGES ----------

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if get_current_user(request):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": None, "mode": "login"},
    )


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    if get_current_user(request):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": None, "mode": "register"},
    )


@app.post("/login")
def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    user = authenticate(username, password)
    if not user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Invalid username or password", "mode": "login"},
            status_code=400,
        )
    response = RedirectResponse("/", status_code=303)
    set_session(response, user)
    return response


@app.post("/register")
def register_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    user, err = create_user(username, password)
    if err:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": err, "mode": "register"},
            status_code=400,
        )
    response = RedirectResponse("/", status_code=303)
    set_session(response, user)
    return response


@app.post("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    clear_session(response)
    return response


# ---------- APP ----------

@app.get("/", response_class=HTMLResponse)
def home(request: Request, tab: str = "home", filter: str = "all"):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    ctx = base_context(user, filter)
    ctx["request"] = request
    ctx["active"] = tab if tab in ("home", "tasks", "decide", "history", "settings") else "home"
    return templates.TemplateResponse(request=request, name="index.html", context=ctx)


@app.post("/tasks/add")
def add_task(
    request: Request,
    title: str = Form(...),
    category: str = Form("Other"),
    priority: int = Form(3),
    estimated_minutes: int = Form(30),
    energy_required: int = Form(50),
    deadline: str = Form(""),
):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    create_task(
        user["id"], title, category, priority, estimated_minutes,
        energy_required, deadline=deadline or None
    )
    return RedirectResponse("/?tab=tasks", status_code=303)


@app.get("/tasks/{task_id}/edit", response_class=HTMLResponse)
def edit_page(request: Request, task_id: int):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    task = get_task(user["id"], task_id)
    if not task:
        return RedirectResponse("/?tab=tasks", status_code=303)

    ctx = base_context(user)
    ctx.update({"request": request, "active": "tasks", "edit_task": task})
    return templates.TemplateResponse(request=request, name="index.html", context=ctx)


@app.post("/tasks/{task_id}/edit")
def edit_save(
    request: Request,
    task_id: int,
    title: str = Form(...),
    category: str = Form("Other"),
    priority: int = Form(3),
    estimated_minutes: int = Form(30),
    energy_required: int = Form(50),
    deadline: str = Form(""),
):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    update_task(
        user["id"], task_id, title, category, priority,
        estimated_minutes, energy_required, deadline or None
    )
    return RedirectResponse("/?tab=tasks", status_code=303)


@app.post("/tasks/{task_id}/complete")
def mark_complete(request: Request, task_id: int):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    complete_task(user["id"], task_id)
    return RedirectResponse("/?tab=tasks", status_code=303)


@app.post("/tasks/{task_id}/delete")
def remove_task(request: Request, task_id: int):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    delete_task(user["id"], task_id)
    return RedirectResponse("/?tab=tasks", status_code=303)


@app.post("/decide", response_class=HTMLResponse)
def decide(
    request: Request,
    mood: str = Form("Neutral"),
    energy: int = Form(50),
    available_time: str = Form("30 min"),
):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    recommendation = get_recommendation(user["id"], mood, energy, available_time)
    ctx = base_context(user)
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
def settings_clear_history(request: Request):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    clear_history(user["id"])
    return RedirectResponse("/?tab=settings", status_code=303)


@app.post("/settings/clear-tasks")
def settings_clear_tasks(request: Request):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    clear_tasks(user["id"])
    return RedirectResponse("/?tab=settings", status_code=303)


@app.get("/export.csv")
def export_csv(request: Request):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    tasks = get_tasks(user["id"])
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id", "title", "category", "priority", "minutes", "energy",
        "deadline", "status", "created_at", "completed_at"
    ])
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