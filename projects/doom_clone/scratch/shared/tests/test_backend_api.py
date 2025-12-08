import importlib.util
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def load_app():
    base_path = Path(__file__).resolve().parent.parent / "backend_api" / "main.py"
    spec = importlib.util.spec_from_file_location("backend_api_main", str(base_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module.app  # type: ignore


def get_client():
    app = load_app()
    return TestClient(app)


@pytest.fixture
def client():
    c = get_client()
    # reset before each test to ensure isolation
    c.post("/reset")
    yield c
    c.post("/reset")


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_resource_success(client):
    resp = client.post("/resources/res1", json={"name": "Resource One"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == "res1"
    assert data["name"] == "Resource One"


def test_create_resource_conflict(client):
    # First create
    resp1 = client.post("/resources/res2", json={"name": "Resource Two"})
    assert resp1.status_code == 201
    # Second create with same id should conflict
    resp2 = client.post("/resources/res2", json={"name": "Resource Two Duplicate"})
    assert resp2.status_code == 409


def test_read_resource_found_and_not_found(client):
    # Create a resource to read
    resp_create = client.post("/resources/res3", json={"name": "Resource Three"})
    assert resp_create.status_code == 201
    # Read existing
    resp_get = client.get("/resources/res3")
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == "res3"
    assert resp_get.json()["name"] == "Resource Three"
    # Read non-existing
    resp_missing = client.get("/resources/missing_id")
    assert resp_missing.status_code == 404


def test_delete_resource(client):
    # Create and then delete
    resp_create = client.post("/resources/res4", json={"name": "Resource Four"})
    assert resp_create.status_code == 201
    resp_del = client.delete("/resources/res4")
    assert resp_del.status_code == 204
    # Ensure it's gone
    resp_get = client.get("/resources/res4")
    assert resp_get.status_code == 404


def test_delete_resource_not_found(client):
    resp = client.delete("/resources/nonexistent")
    assert resp.status_code == 404


def test_invalid_payload_empty_name(client):
    resp = client.post("/resources/res5", json={"name": ""})
    assert resp.status_code == 400
    detail = resp.json().get("detail", "")
    assert "Invalid payload" in detail


def test_create_resource_missing_payload(client):
    resp = client.post("/resources/missing", json={})
    assert resp.status_code == 400
    detail = resp.json().get("detail", "")
    assert "Missing id or data" in detail


def test_create_resource_conflict_different_payload(client):
    # First create
    resp1 = client.post("/resources/conflict1", json={"name": "Alpha"})
    assert resp1.status_code == 201
    # Conflict due to different payload for same id
    resp2 = client.post("/resources/conflict1", json={"name": "Beta"})
    assert resp2.status_code == 409


def test_token_protected_users_no_token(client):
    resp = client.get("/api/users")
    assert resp.status_code == 401 or resp.status_code == 403


def test_token_protected_users_with_token_pagination(client):
    resp = client.get("/api/users?page=1&per_page=1", headers={"Authorization": "Bearer secrettoken"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["per_page"] == 1
    assert "items" in data


def test_get_specific_user_with_token(client):
    resp = client.get("/api/users/u1", headers={"Authorization": "Bearer secrettoken"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "u1"


def test_get_nonexistent_user_with_token(client):
    resp = client.get("/api/users/nonexistent", headers={"Authorization": "Bearer secrettoken"})
    assert resp.status_code == 404


def test_create_user_with_token_success_and_conflict(client):
    resp = client.post("/api/users", json={"id": "u3", "name": "Charlie", "email": "charlie@example.com"}, headers={"Authorization": "Bearer secrettoken"})
    assert resp.status_code == 201
    resp2 = client.post("/api/users", json={"id": "u3", "name": "Charlie2"}, headers={"Authorization": "Bearer secrettoken"})
    assert resp2.status_code == 409


def test_create_user_invalid_payload_empty_name(client):
    resp = client.post("/api/users", json={"id": "u4", "name": ""}, headers={"Authorization": "Bearer secrettoken"})
    assert resp.status_code == 400


def test_token_auth_endpoint_valid_and_invalid(client):
    resp = client.post("/api/token-auth", json={"token": "secrettoken"})
    assert resp.status_code == 200
    resp2 = client.post("/api/token-auth", json={"token": "bad"})
    assert resp2.status_code == 401
