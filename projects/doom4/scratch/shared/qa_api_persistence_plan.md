QA Plan Update: API-backed Persistence

Objective
- Validate that the API-backed persistence layer for editor plans conforms to contract, handles errors gracefully, supports basic auth placeholder, and preserves JSON payloads through end-to-end frontend-to-backend flows.
- Verify editor workflows with live state and regression stability for plan/state endpoints.
- Ensure basic security checks (CORS, data validation) are in place.
- Provide a test matrix across Node/TS/CI where applicable and outline run instructions for CI.

Scope of Endpoints (assumed paths)
- POST /api/editor/plan                 - Create a new editor plan (payload: json plan)
- GET /api/editor/plan/{planId}        - Retrieve a plan by id
- PUT /api/editor/plan/{planId}        - Update an existing plan
- GET /api/editor/plans                  - List all plans
- (Optional) GET /api/editor/plan/{planId}/state - Retrieve live state of a plan

Assumed Request/Response Schemas (contracts)
- Create/Update Payload (example):
  {
    "name": "Sample Plan",
    "config": { "grid": { "width": 10, "height": 10 } },
    "liveState": { "editing": false, "scenario": "default" },
    "version": 1
  }
- Responses: 200/201 with body containing at least {
    "id": "<uuid>",
    "name": string,
    "config": object,
    "liveState": object,
    "version": number,
    "createdAt": "iso-timestamp",
    "updatedAt": "iso-timestamp"
  }
- Error responses: { "error": "string", "code": <int> }

Auth placeholder
- Tests will assume an optional header (e.g., X-Auth-Token or Authorization).
- Without a token: expect 401/403 (or relevant unauthorized response).
- With a token: expect 200/201 for create, and 200 for fetch/update.

Test Scenarios
1) API contract conformance
   - POST valid payload -> 200/201, response contains id and fields match input
   - GET by id -> 200, payload matches stored data
   - PUT by id -> 200, updated fields reflect changes
   - GET list -> 200, returns array with at least the created plan
2) Error handling
   - POST missing required fields -> 400 with error message
   - PUT with invalid payload -> 400
3) Auth placeholder
   - Access without token -> 401/403
   - Access with token -> 200/201
4) End-to-end flow (frontend to backend)
   - Create plan, load via GET, modify, reload, ensure state persists
5) JSON persistence in /api/editor/plan
   - Nested objects under config and liveState are preserved exactly
6) Editor workflows with live state
   - Save and retrieve liveState transitions (e.g., editing true/false)
7) Regression tests for plan/state endpoints
   - Create multiple plans; ensure GET /plans returns them; load individual plan state
8) Security checks
   - CORS preflight returns appropriate Access-Control-Allow-Origin
   - Basic data validation prevents invalid types from being accepted
9) Test matrix and CI
   - Documented matrix for Node/TS/CI environments; run instructions follow.

Environment & Prerequisites
- API_BASE_URL environment variable points to the test server (default http://localhost:3000)
- If authentication token is used in tests, set API_AUTH_TOKEN.
- Python 3.11+ and requests library (pytest as test runner)
- Optional: CI runner with Python and network access.

Test Execution Strategy
- Run: pytest scratch/shared/tests/api_persistence/test_api_persistence.py
- Validate all tests pass if the API server is up with the expected contract.

Security, Validation and Compliance Notes
- Validate input payload strictly; ensure numeric fields are numbers and strings are strings.
- Validate that the API rejects extra/unknown fields gracefully (prefer 400 with a validation error).
- Ensure responses do not leak sensitive data in error messages.

Maintenance
- Update tests when API contract changes; update QA plan accordingly.
- Maintain a small, deterministic test data set to avoid flaky tests.

Appendix: Editor Workflows
- Live state persistence: save liveState along with plan; ensure retrieval returns the same object.
- Editor workflow steps mirror typical UX: create -> edit -> save -> load.

Note: This plan assumes existence of the endpoints and HTTP contract described above. If actual paths differ, adjust tests and docs accordingly.
