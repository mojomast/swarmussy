#!/usr/bin/env python3
import json
import os
import time
import urllib.request
import urllib.error
import requests

BASE_URL = os.environ.get("GRID_API_BASE_URL", "http://localhost:5001")

TEST_CASES = [
    # Health endpoint is unauthenticated
    {"method": "GET", "path": "/health", "headers": {}, "expected_status": 200, "expected_json": {"status": "ok"}},
    # Token-auth path test
    {"method": "POST", "path": "/api/token-auth", "json": {"token": "secrettoken"}, "headers": {}, "expected_status": 200, "expected_json": {"valid": True}},
    # Paginated users with token
    {"method": "GET", "path": "/api/users", "headers": {"Authorization": "Bearer secrettoken"}, "expected_status": 200, "expected_json": None},
    # Get specific user with token
    {"method": "GET", "path": "/api/users/u1", "headers": {"Authorization": "Bearer secrettoken"}, "expected_status": 200, "expected_json": None},
    # Create a new user with token
    {"method": "POST", "path": "/api/users", "json": {"id": "u3", "name": "Test User", "email": "test@example.com"}, "headers": {"Authorization": "Bearer secrettoken"}, "expected_status": 201, "expected_json": None},
    # Get the newly created user
    {"method": "GET", "path": "/api/users/u3", "headers": {"Authorization": "Bearer secrettoken"}, "expected_status": 200, "expected_json": None},
    # Additional contract tests for 400/401/404/409 scenarios
    # 401: unauthorized to access users without token
    {"method": "GET", "path": "/api/users", "headers": {}, "expected_status": 401, "expected_json": None},
    # 400: invalid pagination with page=0
    {"method": "GET", "path": "/api/users?page=0", "headers": {"Authorization": "Bearer secrettoken"}, "expected_status": 400, "expected_json": None},
    # 400: invalid pagination with per_page=0
    {"method": "GET", "path": "/api/users?page=1&per_page=0", "headers": {"Authorization": "Bearer secrettoken"}, "expected_status": 400, "expected_json": None},
    # 200: page beyond data returns empty list (no 404 in this implementation)
    {"method": "GET", "path": "/api/users?page=2", "headers": {"Authorization": "Bearer secrettoken"}, "expected_status": 200, "expected_json": None},
    # 404: non-existent user
    {"method": "GET", "path": "/api/users/unknown", "headers": {"Authorization": "Bearer secrettoken"}, "expected_status": 404, "expected_json": None},
    # 409: duplicate user creation
    {"method": "POST", "path": "/api/users", "json": {"id": "u3", "name": "Test User Duplicate", "email": "dup@example.com"}, "headers": {"Authorization": "Bearer secrettoken"}, "expected_status": 409, "expected_json": None},
    # 401: invalid token on token-auth
    {"method": "POST", "path": "/api/token-auth", "json": {"token": "badtoken"}, "headers": {}, "expected_status": 401, "expected_json": None},
]


def run_test_case(case):
    method = case["method"]
    url = BASE_URL + case["path"]
    headers = case.get("headers", {})
    resp = None
    if method == "GET":
        resp = requests.get(url, headers=headers)
    elif method == "POST":
        resp = requests.post(url, json=case.get("json"), headers=headers)
    elif method == "DELETE":
        resp = requests.delete(url, headers=headers)
    else:
        raise ValueError("Unsupported method")
    ok = resp.status_code == case["expected_status"]
    json_match = True
    if case.get("expected_json") is not None:
        try:
            json_match = resp.json() == case["expected_json"]
        except Exception:
            json_match = False
    return ok and json_match


if __name__ == "__main__":
    results = [run_test_case(c) for c in TEST_CASES]
    print(all(results))
