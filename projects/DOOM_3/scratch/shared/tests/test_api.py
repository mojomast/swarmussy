from fastapi.testclient import TestClient
from scratch.shared.src import server as server_module

# Create a TestClient for the FastAPI app
app = server_module.app
client = TestClient(app)

import uuid

# Helper to create a task
def create_task(project_id: str, token: str, payload: dict):
    headers = {"X-Project-Token": token}
    resp = client.post(f"/projects/{project_id}/tasks", json=payload, headers=headers)
    return resp

# Helper to list tasks

def list_tasks(project_id: str, token: str, status=None):
    headers = {"X-Project-Token": token}
    params = {}
    if status is not None:
        params["status"] = status
    resp = client.get(f"/projects/{project_id}/tasks", headers=headers, params=params)
    return resp

# Test: create task with valid auth
def test_create_task_success():
    project_id = "alpha"
    payload = {
        "title": "Clean park benches",
        "description": "Wipe down benches and sweep surrounding area",
        "due_date": None
    }
    resp = create_task(project_id, "alpha123", payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] is not None
    assert data["project_id"] == project_id
    assert data["title"] == payload["title"]
    assert data["status"] == server_module.TaskStatus.pending

# Test: list tasks contains at least one task from alpha project
def test_list_tasks_in_alpha():
    project_id = "alpha"
    payload = {
        "title": "Water plants",
    }
    resp_create = create_task(project_id, "alpha123", payload)
    assert resp_create.status_code == 201

    resp = list_tasks(project_id, "alpha123")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1

# Test: get a specific task by id
def test_get_task_by_id():
    project_id = "alpha"
    payload = {"title": "Trash pickup"}
    resp_create = create_task(project_id, "alpha123", payload)
    assert resp_create.status_code == 201
    task = resp_create.json()
    task_id = task["id"]

    resp = client.get(f"/projects/{project_id}/tasks/{task_id}", headers={"X-Project-Token": "alpha123"})
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id

# Test: update a task's status

def test_update_task_status():
    project_id = "alpha"
    payload = {"title": "Rake leaves"}
    resp_create = create_task(project_id, "alpha123", payload)
    assert resp_create.status_code == 201
    task = resp_create.json()
    task_id = task["id"]

    resp = client.patch(
        f"/projects/{project_id}/tasks/{task_id}",
        headers={"X-Project-Token": "alpha123"},
        json={"status": server_module.TaskStatus.in_progress}
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["status"] == server_module.TaskStatus.in_progress

# Test: delete a task

def test_delete_task():
    project_id = "alpha"
    payload = {"title": "Sweep sidewalks"}
    resp_create = create_task(project_id, "alpha123", payload)
    assert resp_create.status_code == 201
    task = resp_create.json()
    task_id = task["id"]

    resp = client.delete(
        f"/projects/{project_id}/tasks/{task_id}",
        headers={"X-Project-Token": "alpha123"}
    )
    assert resp.status_code == 204

    # Verify it's gone
    resp_get = client.get(f"/projects/{project_id}/tasks/{task_id}", headers={"X-Project-Token": "alpha123"})
    assert resp_get.status_code == 404

# Test: invalid auth is rejected
def test_invalid_auth_rejected():
    project_id = "alpha"
    payload = {"title": "Test auth"}
    resp = create_task(project_id, "badtoken", payload)
    assert resp.status_code == 403

# Test: non-existent project returns 404
def test_unknown_project_404():
    payload = {"title": "Should fail"}
    resp = create_task("gamma", "gamma123", payload)
    assert resp.status_code == 404
