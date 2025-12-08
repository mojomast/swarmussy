#!/usr/bin/env python3
"""
Grid API QA test harness

This test suite is designed to be run inside the CI harness. It uses
only the Python standard library to avoid external dependencies.

Environment:
  GRID_API_BASE_URL: Base URL for the grid API (e.g., http://localhost:8000/api)
  GRID_API_TOKEN: Bearer token for authenticated requests (optional for open endpoints)

Test Coverage:
  - List grids (GET /grids)
  - Error handling when no/invalid auth is supplied
  - Asset lifecycle (POST /assets, GET, PATCH, DELETE)
"""

import os
import json
import time
import ssl
import urllib.request
import urllib.parse
from urllib.error import HTTPError

# Optional pytest support: tests will gracefully skip if env not configured
try:
    import pytest
except Exception:
    pytest = None

# Normalized API helpers
BASE_URL = os.environ.get("GRID_API_BASE_URL")  # e.g., https://ci-harness.local/api
TOKEN = os.environ.get("GRID_API_TOKEN", None)

# Safety: ensure we always use a sane timeout
TIMEOUT = 15

# Disable SSL certificate verification for local CI harness scenarios
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def _make_request(path, method="GET", data=None, token=None, base_url=None):
    if base_url is None:
        base_url = BASE_URL
    if not base_url:
        raise RuntimeError("GRID_API_BASE_URL not configured. Set GRID_API_BASE_URL environment variable.")

    if not path.startswith("/"):
        path = "/" + path
    url = base_url.rstrip("/") + path

    body = None
    headers = {
        "Accept": "application/json",
    }
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ssl_context) as resp:
            resp_body = resp.read()
            content_type = resp.headers.get("Content-Type", "")
            if resp_body:
                if "application/json" in content_type or resp_body.strip().startswith(b"{"):
                    return resp.status, json.loads(resp_body.decode("utf-8"))
                else:
                    return resp.status, resp_body.decode("utf-8", errors="replace")
            return resp.status, None
    except HTTPError as e:
        # Non-2xx responses
        code = e.code
        try:
            payload = e.read().decode("utf-8")
            payload_json = json.loads(payload) if payload else None
        except Exception:
            payload_json = None
        return code, payload_json or {"error": e.reason}
    except Exception as e:
        return None, {"error": str(e)}


def _require_configured():
    if BASE_URL:
        return True
    return False


# Pytest-compatible tests

def test_list_grids_flow():
    # Ensure we are configured
    if not _require_configured():
        import pytest
        pytest.skip("GRID_API_BASE_URL not configured")

    # Step 1: list grids with authentication (if token present)
    status, payload = _make_request("/grids", method="GET", token=TOKEN)
    assert status in (200, 401, 403, 0)  # some endpoints may be public or require auth
    if status == 200:
        assert isinstance(payload, list)
        # Basic shape checks if list not empty
        if payload:
            item = payload[0]
            assert "id" in item
            assert "name" in item
    else:
        # non-200: ensure proper error shape returned
        assert isinstance(payload, dict)


def test_error_states():
    if not _require_configured():
        import pytest
        pytest.skip("GRID_API_BASE_URL not configured")

    # Access with invalid token if token required to exercise 401/403
    # We'll try two variations: invalid token and invalid path
    if TOKEN:
        status, payload = _make_request("/grids", method="GET", token="invalid-token")
        assert status in (401, 403)
        assert payload is not None
    # Invalid path should yield 404
    status, payload = _make_request("/grid-does-not-exist", method="GET", token=TOKEN)
    assert status in (404, 400)
    # Ensure a structured error payload or text
    assert payload is None or isinstance(payload, dict)


def test_asset_lifecycle():
    if not _require_configured():
        import pytest
        pytest.skip("GRID_API_BASE_URL not configured")

    if not BASE_URL or not BASE_URL.strip():
        import pytest
        pytest.skip("GRID_API_BASE_URL not configured")

    # Create an asset
    asset_payload = {
        "name": "qa-test-asset",
        "type": "image",
        "data": {
            "dummy": True,
            "seed": 1234
        }
    }
    status, resp = _make_request("/assets", method="POST", data=asset_payload, token=TOKEN)
    assert status in (200, 201)
    asset_id = None
    if isinstance(resp, dict):
        asset_id = resp.get("id") or resp.get("asset_id")
    if not asset_id:
        # Sometimes API returns the asset in response
        asset_id = resp.get("id") if isinstance(resp, dict) else None
    assert asset_id is not None, f"Asset creation did not return id. Response: {resp}"

    # Read asset
    status, resp = _make_request(f"/assets/{asset_id}", method="GET", token=TOKEN)
    assert status in (200,)

    # Update asset name
    update_payload = {"name": "qa-test-asset-renamed"}
    status, resp = _make_request(f"/assets/{asset_id}", method="PATCH", data=update_payload, token=TOKEN)
    assert status in (200, 204)

    # Delete asset
    status, resp = _make_request(f"/assets/{asset_id}", method="DELETE", token=TOKEN)
    assert status in (200, 204, 202)

    # Confirm delete
    status, resp = _make_request(f"/assets/{asset_id}", method="GET", token=TOKEN)
    assert status in (404, 410)


# Optional: grid export/import flow if API supports it

def test_grid_export_import():
    if not _require_configured():
        import pytest
        pytest.skip("GRID_API_BASE_URL not configured")

    # Attempt to fetch the first grid and export/import if supported
    status, grids = _make_request("/grids", method="GET", token=TOKEN)
    if status != 200 or not isinstance(grids, list) or len(grids) == 0:
        import pytest
        pytest.skip("No grids available for export/import test or API not exposing /grids list")

    grid_id = grids[0].get("id") if isinstance(grids[0], dict) else None
    if not grid_id:
        import pytest
        pytest.skip("First grid missing id; cannot perform export/import test")

    # Try export
    status, export_payload = _make_request(f"/grids/{grid_id}/export", method="POST", token=TOKEN)
    if status not in (200, 201):
        # If export isn't supported, skip gracefully
        import pytest
        pytest.skip("Grid export not supported by API")

    if isinstance(export_payload, dict):
        export_payload_body = export_payload
    else:
        export_payload_body = {}

    # Try import with exported content
    status, import_resp = _make_request("/grids/import", method="POST", data=export_payload_body, token=TOKEN)
    assert status in (200, 201, 202, 204)
