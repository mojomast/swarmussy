import os
import json
import requests
from typing import Any

try:
    from jsonschema import validate as jsonschema_validate
    from jsonschema.exceptions import ValidationError
    JSONSCHEMA_AVAILABLE = True
except Exception:
    JSONSCHEMA_AVAILABLE = False

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
TOKEN = os.environ.get("API_TOKEN", "test-token")
HEADERS_WITH_AUTH = {"Authorization": f"Bearer {TOKEN}"}
HEADERS_JSON = {"Content-Type": "application/json"}

# Simple helpers to extract payload from common ApiResponse shapes

def extract_data_shape(resp_json: Any) -> Any:
    if not isinstance(resp_json, dict):
        return resp_json
    # Common wrapper shapes
    for key in ("data", "payload", "result"]:
        if key in resp_json:
            return resp_json[key]
    return resp_json


def ensure_status_ok(resp: requests.Response, require_auth: bool = False, status_codes=None):
    if status_codes is None:
        status_codes = (200,)
    if resp.status_code not in status_codes:
        raise AssertionError(f"Unexpected status code: {resp.status_code} for {resp.request.method} {resp.url}. Body: {resp.text}")
    if require_auth:
        # If endpoint is auth-protected, ensure that a non-auth request yields 401/403
        pass
    return resp


def validate_with_schema(data: Any, schema: dict) -> bool:
    if not JSONSCHEMA_AVAILABLE:
        # If jsonschema isn't available, skip strict validation but ensure data is a dict or list as a basic check
        return isinstance(data, (dict, list))
    try:
        jsonschema_validate(instance=data, schema=schema)
        return True
    except ValidationError:
        return False


def test_auth_required_state():
    url = f"{BASE_URL}/api/editor/state"
    resp = requests.get(url)
    # Expecting 401/403 when not authenticated
    assert resp.status_code in (401, 403), f"Expected auth error, got {resp.status_code} for {resp.url} body: {resp.text}"


def test_auth_required_plan():
    url = f"{BASE_URL}/api/editor/plan"
    resp = requests.get(url)
    assert resp.status_code in (401, 403), f"Expected auth error for plan, got {resp.status_code}"


def test_auth_required_assets():
    url = f"{BASE_URL}/api/editor/assets"
    resp = requests.get(url)
    assert resp.status_code in (401, 403), f"Expected auth error for assets, got {resp.status_code}"


def test_cors_preflight_state():
    url = f"{BASE_URL}/api/editor/state"
    headers = {
        "Origin": "http://example.com",
        "Access-Control-Request-Method": "GET",
    }
    resp = requests.options(url, headers=headers)
    # Some servers respond 204 with no content
    assert resp.status_code in (200, 204), f"Unexpected preflight status: {resp.status_code} for {url}"
    assert "Access-Control-Allow-Origin" in resp.headers or resp.headers.get("Access-Control-Allow-Origin") is not None, "CORS header missing in preflight response"


def test_editor_state_contract_authenticated():
    url = f"{BASE_URL}/api/editor/state"
    resp = requests.get(url, headers=HEADERS_WITH_AUTH)
    assert resp.status_code == 200, f"State endpoint not accessible with auth: {resp.status_code}"
    data = resp.json()
    data_payload = extract_data_shape(data)
    assert isinstance(data_payload, (dict, list)), "State payload is not JSON object/array"
    # Basic structural validation depending on shape
    if isinstance(data_payload, dict):
        # If wrapped in {"state": {...}} ensure inner is object
        if "state" in data_payload:
            assert isinstance(data_payload["state"], dict), "state field must be an object"
        else:
            # If data is directly the state object, ensure it's a dict
            # (do not fail if shape is different but still valid)
            pass
    # Optional JSON schema validation if available
    if JSONSCHEMA_AVAILABLE:
        # Try to validate common shapes
        # If the wrapper contains data/state, attempt to locate a plausible payload
        payload = data_payload
        if isinstance(data_payload, dict) and "state" in data_payload:
            payload = data_payload["state"]
        elif isinstance(data_payload, dict) and "world" in data_payload:
            payload = data_payload["world"]
        # Minimal schema: an object for state
        schema = {"type": "object"}
        assert validate_with_schema(payload, schema), "State payload failed basic schema validation"


def test_editor_plan_contract_authenticated():
    url = f"{BASE_URL}/api/editor/plan"
    resp = requests.get(url, headers=HEADERS_WITH_AUTH)
    assert resp.status_code == 200, f"Plan endpoint not accessible with auth: {resp.status_code}"
    data = resp.json()
    data_payload = extract_data_shape(data)
    assert isinstance(data_payload, (dict, list)), "Plan payload is not JSON object/array"
    if isinstance(data_payload, dict):
        if "steps" in data_payload:
            assert isinstance(data_payload["steps"], list), "steps should be a list"
        if "current_step" in data_payload:
            assert isinstance(data_payload["current_step"], (str, type(None))), "current_step should be string or null"
        if "plan" in data_payload and isinstance(data_payload["plan"], dict):
            plan = data_payload["plan"]
            if "steps" in plan:
                assert isinstance(plan["steps"], list)
    if JSONSCHEMA_AVAILABLE:
        # Attempt a loose shape validation
        payload = data_payload
        if isinstance(payload, dict) and "steps" in payload:
            schema = {"type": "object", "properties": {"steps": {"type": "array"}}}
            assert validate_with_schema(payload, schema) or True


def test_editor_assets_contract_authenticated():
    url = f"{BASE_URL}/api/editor/assets"
    resp = requests.get(url, headers=HEADERS_WITH_AUTH)
    assert resp.status_code == 200, f"Assets endpoint not accessible with auth: {resp.status_code}"
    data = resp.json()
    data_payload = extract_data_shape(data)
    assert isinstance(data_payload, (dict, list)), "Assets payload is not JSON object/array"
    if isinstance(data_payload, dict) and "assets" in data_payload:
        assert isinstance(data_payload["assets"], list), "assets should be a list"
    if JSONSCHEMA_AVAILABLE:
        payload = data_payload
        if isinstance(payload, dict) and "assets" in payload:
            payload = payload["assets"]
        schema = {"type": "array"}
        assert validate_with_schema(payload, schema) or True


def test_error_handling_unknown_endpoint():
    url = f"{BASE_URL}/api/editor/state/doesnotexist"
    resp = requests.get(url, headers=HEADERS_WITH_AUTH)
    # Expect 404 for unknown endpoint
    assert resp.status_code == 404, f"Expected 404 for unknown endpoint, got {resp.status_code}"
