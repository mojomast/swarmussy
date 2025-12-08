from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import Optional, List, Dict
import uuid
from datetime import datetime

# New pluggable repository for tasks (in-memory first)
try:
    from shared.infra.cleanup.app.repository.in_memory_repo import InMemoryRepo as InMemoryTaskRepo
    _REPO = InMemoryTaskRepo()
except Exception:
    _REPO = None  # Fallback if import fails

# In-memory per-project storage (legacy fallback, kept for compatibility if repo not available)
_PROJECT_STORE: Dict[str, Dict[str, 'Task']] = {}

_PROJECT_REGISTRY: Dict[str, Dict[str, str]] = {
    "alpha": {"token": "alpha123"},
    "beta": {"token": "betatoken"},
}

class TaskStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    done = "done"

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, description="Title of the task")
    description: Optional[str] = Field(None, description="Optional description of the task")
    status: Optional[TaskStatus] = Field(TaskStatus.pending, description="Initial status")
    due_date: Optional[str] = Field(None, description="Due date in ISO 8601 format (YYYY-MM-DD or full datetime)")

    @validator('due_date')
    def validate_due_date(cls, v):
        if v is None:
            return v
        try:
            datetime.fromisoformat(v.rstrip('Z'))
        except Exception:
            raise ValueError("due_date must be a valid ISO 8601 date/time string")
        return v

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[str] = None

class Task(BaseModel):
    id: str
    project_id: str
    title: str
    description: Optional[str] = None
    status: TaskStatus
    due_date: Optional[str] = None
    created_at: str
    updated_at: str

app = FastAPI(title="Cleanup Tasks API", version="1.0.0")


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec='seconds') + 'Z'


def _get_store_for_project(project_id: str) -> Dict[str, Task]:
    if project_id not in _PROJECT_REGISTRY:
        raise HTTPException(status_code=404, detail="Project not found")
    return _PROJECT_STORE.setdefault(project_id, {})


def _authenticate(project_id: str, x_token: Optional[str] = Header(None, alias="X-Project-Token")):
    reg = _PROJECT_REGISTRY.get(project_id)
    if not reg:
        raise HTTPException(status_code=404, detail="Project not found")
    if not x_token or x_token != reg["token"]:
        raise HTTPException(status_code=403, detail="Invalid authentication token")
    return True


@app.post("/projects/{project_id}/tasks", response_model=Task, status_code=201)
def create_task(project_id: str, payload: TaskCreate, authenticated: bool = Depends(_authenticate)):
    _ = authenticated
    # Try repository first
    if _REPO is not None:
        data = payload.dict(exclude_none=True)
        return _REPO.create_task(project_id, data)
    # Fallback to legacy in-memory store
    store = _get_store_for_project(project_id)
    task_id = str(uuid.uuid4())
    now = _now_iso()
    task = {
        "id": task_id,
        "project_id": project_id,
        "title": payload.title,
        "description": payload.description,
        "status": (payload.status or TaskStatus.pending),
        "due_date": payload.due_date,
        "created_at": now,
        "updated_at": now,
    }
    store[task_id] = task
    return task


@app.get("/projects/{project_id}/tasks", response_model=List[Task])
def list_tasks(project_id: str, status: Optional[TaskStatus] = None, limit: int = 100, offset: int = 0, authenticated: bool = Depends(_authenticate)):
    _ = authenticated
    if _REPO is not None:
        items = _REPO.list_tasks(project_id)
        if status is not None:
            items = [t for t in items if t.get('status') == status]
        items = sorted(items, key=lambda x: x.get('created_at', ''))
        return items[offset: offset + limit]
    store = _get_store_for_project(project_id)
    items = list(store.values())
    if status is not None:
        items = [t for t in items if t.get('status') == status]
    items.sort(key=lambda t: t['created_at'])
    return items[offset: offset + limit]


@app.get("/projects/{project_id}/tasks/{task_id}", response_model=Task)
def get_task(project_id: str, task_id: str, authenticated: bool = Depends(_authenticate)):
    _ = authenticated
    if _REPO is not None:
        task = _REPO.get_task(project_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    store = _get_store_for_project(project_id)
    task = store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/projects/{project_id}/tasks/{task_id}", response_model=Task)
def update_task(project_id: str, task_id: str, payload: TaskUpdate, authenticated: bool = Depends(_authenticate)):
    _ = authenticated
    if _REPO is not None:
        updates = payload.dict(exclude_none=True)
        updated = _REPO.update_task(project_id, task_id, updates)  # type: ignore
        if updated is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return updated
    store = _get_store_for_project(project_id)
    task = store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if payload.title is not None:
        task["title"] = payload.title
    if payload.description is not None:
        task["description"] = payload.description
    if payload.status is not None:
        task["status"] = payload.status
    if payload.due_date is not None:
        task["due_date"] = payload.due_date
    task["updated_at"] = _now_iso()
    store[task_id] = task
    return task


@app.delete("/projects/{project_id}/tasks/{task_id}", status_code=204)
def delete_task(project_id: str, task_id: str, authenticated: bool = Depends(_authenticate)):
    _ = authenticated
    if _REPO is not None:
        ok = _REPO.delete_task(project_id, task_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Task not found")
        return
    store = _get_store_for_project(project_id)
    if task_id in store:
        del store[task_id]
        return
    raise HTTPException(status_code=404, detail="Task not found")
