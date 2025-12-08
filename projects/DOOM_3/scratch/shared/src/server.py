from __future__ import annotations

from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import Optional, List, Dict
import uuid
from datetime import datetime
import os
import json

# Simple, pluggable repository backend selection
REPO_BACKEND = os.environ.get("REPO_BACKEND", "memory")
REPO_STORE_FILE = os.environ.get("REPO_STORE_FILE", os.path.join(os.path.dirname(__file__), 'repo_store.json'))

# In-memory per-project storage (pluggable DB later)
_PROJECT_STORE: Dict[str, Dict[str, 'Task']] = {}

# Try to load filesystem-backed repository state if enabled
def _load_repo_state():
    global _PROJECT_STORE
    if REPO_BACKEND != 'filesystem':
        return
    if os.path.exists(REPO_STORE_FILE):
        try:
            with open(REPO_STORE_FILE, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            for project_id, tasks in raw.items():
                if project_id not in _PROJECT_STORE:
                    _PROJECT_STORE[project_id] = {}
                for task_id, tdict in (tasks or {}).items():
                    if isinstance(tdict, dict):
                        try:
                            task = Task(**tdict)  # type: ignore[arg-type]
                        except Exception:
                            # Fallback: create minimal Task
                            task = Task(
                                id=tdict.get('id', task_id),
                                project_id=project_id,
                                title=tdict.get('title', ''),
                                description=tdict.get('description'),
                                status=tdict.get('status', 'pending'),
                                due_date=tdict.get('due_date'),
                                created_at=tdict.get('created_at', datetime.utcnow().isoformat()),
                                updated_at=tdict.get('updated_at', datetime.utcnow().isoformat()),
                            )
                        _PROJECT_STORE[project_id][task_id] = task
        except Exception:
            # If load fails, start fresh with empty store
            _PROJECT_STORE = {}
_load_repo_state()

# Persist repository state to file if filesystem backend is used
def _dump_repo_state():
    if REPO_BACKEND != 'filesystem':
        return
    # Serialize to JSON-friendly structure
    data: Dict[str, Dict[str, dict]] = {}
    for pid, tasks in _PROJECT_STORE.items():
        data[pid] = {tid: t.dict() for tid, t in tasks.items()}  # type: ignore[arg-type]
    os.makedirs(os.path.dirname(REPO_STORE_FILE) or '.', exist_ok=True)
    with open(REPO_STORE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

# Simple, in-memory project registry with tokens for auth (per-project scoping)
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

# Ensure a project store exists for a project when accessed
def _get_store_for_project(project_id: str) -> Dict[str, Task]:
    if project_id not in _PROJECT_REGISTRY:
        raise HTTPException(status_code=404, detail="Project not found")
    # Ensure store exists for this project
    if project_id not in _PROJECT_STORE:
        _PROJECT_STORE[project_id] = {}
    return _PROJECT_STORE[project_id]

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
    store = _get_store_for_project(project_id)
    task_id = str(uuid.uuid4())
    now = _now_iso()
    task = Task(
        id=task_id,
        project_id=project_id,
        title=payload.title,
        description=payload.description,
        status=payload.status or TaskStatus.pending,
        due_date=payload.due_date,
        created_at=now,
        updated_at=now,
    )
    store[task_id] = task
    _dump_repo_state()
    return task

@app.get("/projects/{project_id}/tasks", response_model=List[Task])
def list_tasks(project_id: str, status: Optional[TaskStatus] = None, limit: int = 100, offset: int = 0, authenticated: bool = Depends(_authenticate)):
    _ = authenticated
    store = _get_store_for_project(project_id)
    items = list(store.values())
    if status is not None:
        items = [t for t in items if t.status == status]
    items.sort(key=lambda t: t.created_at)
    return items[offset : offset + limit]

@app.get("/projects/{project_id}/tasks/{task_id}", response_model=Task)
def get_task(project_id: str, task_id: str, authenticated: bool = Depends(_authenticate)):
    _ = authenticated
    store = _get_store_for_project(project_id)
    task = store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.patch("/projects/{project_id}/tasks/{task_id}", response_model=Task)
def update_task(project_id: str, task_id: str, payload: TaskUpdate, authenticated: bool = Depends(_authenticate)):
    _ = authenticated
    store = _get_store_for_project(project_id)
    task = store.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    updated = False
    if payload.title is not None:
        task.title = payload.title
        updated = True
    if payload.description is not None:
        task.description = payload.description
        updated = True
    if payload.status is not None:
        task.status = payload.status
        updated = True
    if payload.due_date is not None:
        task.due_date = payload.due_date
        updated = True
    if updated:
        task.updated_at = _now_iso()
    store[task_id] = task
    _dump_repo_state()
    return task

@app.delete("/projects/{project_id}/tasks/{task_id}", status_code=204)
def delete_task(project_id: str, task_id: str, authenticated: bool = Depends(_authenticate)):
    _ = authenticated
    store = _get_store_for_project(project_id)
    if task_id in store:
        del store[task_id]
        _dump_repo_state()
        return
    raise HTTPException(status_code=404, detail="Task not found")

# Initialize store lazily for test/startup; load on import
# Endpoints expose health and basic management for tests in repository-backed mode
