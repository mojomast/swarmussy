import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient
import pytest


def load_app():
    base_path = Path(__file__).resolve().parent.parent / "backend_api" / "main.py"
    spec = importlib.util.spec_from_file_location("backend_api_expanded", str(base_path))
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


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_users_unauthorized(client):
    resp = client.get("/api/users")
    assert resp.status_code == 401


def test_users_invalid_pagination_400s(client):
    tok = {"Authorization": "Bearer secrettoken"}
    resp = client.get("/api/users?page=0", headers=tok)
    assert resp.status_code == 400
    resp = client.get("/api/users?limit=0", headers=tok)
    assert resp.status_code == 400


def test_users_pagination_authorized(client):
    tok = {"Authorization": "Bearer secrettoken"}
    resp = client.get("/api/users?page=1&limit=1", headers=tok)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("page", 0) == 1
    assert data.get("per_page", 0) == 1
    assert isinstance(data.get("items"), list)


def test_get_user_existing_and_not_found(client):
    tok = {"Authorization": "Bearer secrettoken"}
    resp = client.get("/api/users/u1", headers=tok)
    assert resp.status_code == 200
    assert isinstance(resp.json(), dict)

    resp = client.get("/api/users/nonexistent", headers=tok)
    assert resp.status_code == 404


def test_create_user_with_token_and_duplicate(client):
    tok = {"Authorization": "Bearer secrettoken"}
    payload = {"id": "u3", "name": "Charlie", "email": "charlie@example.com"}
    resp = client.post("/api/users", json=payload, headers=tok)
    assert resp.status_code == 201
    resp2 = client.post("/api/users", json=payload, headers=tok)
    assert resp2.status_code == 409


def test_create_user_with_invalid_payload_missing_name(client):
    tok = {"Authorization": "Bearer secrettoken"}
    payload = {"id": "u4", "email": "x@example.com"}
    resp = client.post("/api/users", json=payload, headers=tok)
    assert resp.status_code == 422


def test_token_auth_endpoint_valid_and_invalid(client):
    resp = client.post("/api/token-auth", json={"token": "secrettoken"})
    assert resp.status_code == 200
    resp2 = client.post("/api/token-auth", json={"token": "bad"})
    assert resp2.status_code == 401


def test_pagination_beyond_data_returns_404(client):
    resp = client.get("/api/users?page=2", headers={"Authorization": "Bearer secrettoken"})
    assert resp.status_code == 404
