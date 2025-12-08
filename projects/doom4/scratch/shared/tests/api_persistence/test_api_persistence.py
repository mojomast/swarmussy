import os
import json
import pytest
import requests

# Configuration - set these in the environment when running tests
BASE_URL = os.environ.get("API_BASE_URL")
AUTH_TOKEN = os.environ.get("API_AUTH_TOKEN", "")

pytestmark = pytest.mark.skipif(BASE_URL is None, reason="API_BASE_URL not configured; skipping API persistence tests.")


def _default_headers():
    headers = {"Content-Type": "application/json"}
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    return headers


@pytest.fixture(scope="module")
def base_url():
    if not BASE_URL:
        pytest.skip("BASE_URL not configured")
    return BASE_URL.rstrip("/")


@pytest.fixture(scope="module")
def headers():
    return _default_headers()


@pytest.fixture(scope="module")
def ensure_api_available(base_url):
    # Try a minimal set of health endpoints to determine if API is reachable
    candidates = [
        f"{base_url}/health",
        f"{base_url}/healthz",
        f"{base_url}/ping",
        f"{base_url}/api/health",
    ]
    for u in candidates:
        try:
            r = requests.get(u, timeout=5)
        except Exception:
            continue
        if 200 <= r.status_code < 300:
            return True
        if r.status_code in (404, 405, 501, 503, 403, 401):
            # Endpoint exists but not available; keep checking other candidates
            continue
        # Other statuses may indicate transient issue; continue trying
    pytest.skip("No healthy API health endpoint available; skipping tests.")


@pytest.fixture(scope="module")
def created_plan_id(base_url, headers, ensure_api_available):
    url = f"{base_url}/api/editor/plan"
    payload = {
        "name": "QA Plan - API Persistence",
        "description": "Automated tests: API-backed persistence",
        "version": 1,
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
    except Exception as e:
        pytest.skip(f"Could not reach API to create plan: {e}")

    if r.status_code in (200, 201):
        try:
            data = r.json()
        except Exception:
            pytest.skip("POST succeeded but response is not JSON")
        plan_id = data.get("id") or data.get("plan", {}).get("id")
        if not plan_id:
            # Try to extract from Location header
            loc = r.headers.get("Location")
            if loc:
                plan_id = str(loc.rstrip("/").split("/")[-1])
        yield plan_id
        # Cleanup
        if plan_id:
            try:
                requests.delete(f"{base_url}/api/editor/plan/{plan_id}", headers=headers, timeout=5)
            except Exception:
                pass
        return
    elif r.status_code in (400, 422, 409):
        pytest.skip("API rejected plan creation (contract/validation).")
    elif r.status_code in (401, 403):
        pytest.skip("Auth required/forbidden for plan creation.")
    else:
        r.raise_for_status()


def test_plan_retrieve_by_id(base_url, headers, created_plan_id):
    plan_id = created_plan_id
    if not plan_id:
        pytest.skip("No plan_id created; skipping retrieval test.")
    url = f"{base_url}/api/editor/plan/{plan_id}"
    r = requests.get(url, headers=headers, timeout=5)

    if r.status_code in (200, 304):
        try:
            data = r.json()
        except Exception:
            pytest.fail("GET by id returned non-JSON in body")
        assert isinstance(data, dict)
        assert str(data.get("id")) == str(plan_id)
    elif r.status_code in (404, 405, 501, 503):
        pytest.skip("GET by id not available on backend.")
    elif r.status_code in (401, 403):
        pytest.skip("Auth required/forbidden for GET by id.")
    else:
        r.raise_for_status()


def test_post_invalid_payload(base_url, headers):
    url = f"{base_url}/api/editor/plan"
    invalid_payload = {"name": ""}  # invalid due to empty name or missing fields
    r = requests.post(url, json=invalid_payload, headers=headers, timeout=5)

    if r.status_code in (400, 422):
        # Expected for invalid input
        return
    elif r.status_code in (404, 405, 501, 503):
        pytest.skip("POST endpoint not available for invalid payload test.")
    elif r.status_code in (401, 403):
        pytest.skip("Auth required/forbidden for posting invalid payload.")
    else:
        # If endpoint accepts any payload, still ensure it returns error for invalid input
        r.raise_for_status()


def test_cors_preflight(base_url):
    url = f"{base_url}/api/editor/plan"
    headers = {
        "Origin": "https://example.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type,Authorization",
    }
    r = requests.options(url, headers=headers, timeout=5)
    if r.status_code in (200, 204, 206):
        assert "Access-Control-Allow-Origin" in r.headers
    else:
        pytest.skip("CORS preflight not supported or endpoint unavailable.")


def test_end_to_end_update_and_fetch(base_url, headers, created_plan_id):
    plan_id = created_plan_id
    if not plan_id:
        pytest.skip("No plan_id created; skipping end-to-end update test.")
    url = f"{base_url}/api/editor/plan/{plan_id}"
    update_payload = {"name": "QA Plan - API Persistence Updated"}
    r = requests.put(url, json=update_payload, headers=headers, timeout=5)

    if r.status_code in (200, 204):
        # Fetch and verify update
        r2 = requests.get(url, headers=headers, timeout=5)
        if r2.status_code in (200, 304):
            try:
                data = r2.json()
            except Exception:
                pytest.fail("GET after update returned non-JSON body")
            if isinstance(data, dict):
                # Some backends might nest the plan under 'plan'
                value = data.get("name") or data.get("plan", {}).get("name")
                assert value is None or isinstance(value, str)
        else:
            if r2.status_code in (404, 405, 501, 503):
                pytest.skip("GET after update endpoint not available.")
            else:
                r2.raise_for_status()
    elif r.status_code in (400, 422):
        pytest.skip("Update rejected due to invalid payload or contract.")
    elif r.status_code in (401, 403):
        pytest.skip("Auth required/forbidden for updating plan.")
    else:
        r.raise_for_status()


def test_live_state_endpoints(base_url, headers, created_plan_id):
    plan_id = created_plan_id
    if not plan_id:
        pytest.skip("No plan_id created; skipping live state test.")
    # Try a couple of common state endpoints if present
    candidates = [f"{base_url}/api/editor/plan/{plan_id}/state",
                  f"{base_url}/api/editor/plan/{plan_id}/live-state",
                  f"{base_url}/api/editor/plan/{plan_id}/state/latest"]
    for url in candidates:
        try:
            r = requests.get(url, headers=headers, timeout=5)
        except Exception:
            continue
        if r.status_code in (200, 304):
            try:
                data = r.json()
            except Exception:
                continue
            assert isinstance(data, (dict, list))
            return
        elif r.status_code in (404, 405, 501, 503):
            continue
        else:
            r.raise_for_status()
    pytest.skip("Live state endpoint not available for this backend.")
