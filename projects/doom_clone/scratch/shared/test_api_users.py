import json
from fastapi.testclient import TestClient

# Import the FastAPI app from the backend API module
from shared.backend_api.main import app

client = TestClient(app)


def auth_headers(token: str = 'secrettoken'):
    return {'Authorization': f'Bearer {token}'}


def test_get_users_unauthorized_returns_401():
    r = client.get('/api/users')
    assert r.status_code == 401


def test_get_users_with_token_returns_200():
    r = client.get('/api/users', headers=auth_headers())
    assert r.status_code == 200
    data = r.json()
    assert 'items' in data or 'page' in data


def test_get_user_by_id_success():
    r = client.get('/api/users/u1', headers=auth_headers())
    assert r.status_code == 200
    assert r.json().get('id') == 'u1'


def test_get_user_not_found():
    r = client.get('/api/users/unknown', headers=auth_headers())
    assert r.status_code == 404


def test_pagination_invalid_page():
    r = client.get('/api/users?page=0', headers=auth_headers())
    assert r.status_code == 400


def test_pagination_invalid_per_page():
    r = client.get('/api/users?page=1&per_page=0', headers=auth_headers())
    assert r.status_code == 400


def test_create_user_and_duplicate():
    payload = { 'id': 'u3', 'name': 'Test User', 'email': 'test@example.com' }
    r = client.post('/api/users', json=payload, headers=auth_headers())
    # Should create successfully
    assert r.status_code == 201
    assert r.json().get('id') == 'u3'
    # Duplicate should 409
    r2 = client.post('/api/users', json=payload, headers=auth_headers())
    assert r2.status_code == 409


def test_token_auth_success_and_failure():
    r = client.post('/api/token-auth', json={'token': 'secrettoken'})
    assert r.status_code == 200
    assert r.json() == {'valid': True}

    r2 = client.post('/api/token-auth', json={'token': 'bad'})
    assert r2.status_code == 401
