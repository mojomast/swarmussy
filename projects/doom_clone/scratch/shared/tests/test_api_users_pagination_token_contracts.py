import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient
import pytest


def load_app():
    base_path = Path(__file__).resolve().parent.parent / "backend_api" / "main.py"
    spec = importlib.util.spec_from_file_location("backend_api_contracts_ext", str(base_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module.app  # type: ignore


def get_client():
    app = load_app()
    return TestClient(app)


@pytest.fixture
def client():
    c = get_client()
    # reset to ensure isolation
    c.post("/reset")
    yield c
    c.post("/reset")


def test_unauthorized_access_users(client):
    resp = client.get("/api/users")
    assert resp.status_code == 401


def test_pagination_400s_on_invalid_params(client):
    resp = client.get("/api/users?page=0", headers={"Authorization": "Bearer secrettoken"})
    assert resp.status_code == 400
    resp = client.get("/api/users?page=1&limit=0", headers={"Authorization": "Bearer secrettoken"})
    assert resp.status_code == 400


def test_pagination_authorized_basic(client):
    resp = client.get("/api/users?page=1&limit=1", headers={"Authorization": "Bearer secrettoken"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("page") == 1
    assert data.get("per_page") == 1
    assert isinstance(data.get("items"), list)


def test_get_user_by_id_with_token(client):
    resp = client.get("/api/users/u1", headers={"Authorization": "Bearer secrettoken"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("id") == 'u1'


def test_get_user_by_id_not_found_with_token(client):
    resp = client.get("/api/users/nonexistent", headers={"Authorization": "Bearer secrettoken"})
    assert resp.status_code == 404


def test_create_user_with_token_and_duplicate(client):
    payload = {"id": "u3", "name": "Charlie", "email": "charlie@example.com"}
    resp = client.post("/api/users", json=payload, headers={"Authorization": "Bearer secrettoken"})
    assert resp.status_code == 201
    resp2 = client.post("/api/users", json=payload, headers={"Authorization": "Bearer secrettoken"})
    assert resp2.status_code == 409


def test_create_user_invalid_payload_missing_name_with_token(client):
    payload = {"id": "u4", "email": "x@example.com"}
    resp = client.post("/api/users", json=payload, headers={"Authorization": "Bearer secrettoken"})
    # 422 due to missing required field 'name'
    assert resp.status_code == 422


def test_token_auth_endpoint_valid_and_invalid(client):
    resp = client.post("/api/token-auth", json={"token": "secrettoken"})
    assert resp.status_code == 200
    resp2 = client.post("/api/token-auth", json={"token": "bad"})
    assert resp2.status_code == 401
