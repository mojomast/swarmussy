Phase 2 OpenAPI Extension - Quick Handoff

Scope (concise):
- Implement Phase 2 API surface for engine/controller and runtime data under /v2/:
  - GET /v2/editor/level
  - POST /v2/editor/level
  - GET /v2/engine/render_stats
  - GET /v2/events/stream (Server-Sent Events)
- Align request/response payloads and error shapes with Phase 1 contracts.
- Wire into runtime surface: server_api_v2.py and server_orchestrator.py; extend tests in shared/tests/api/test_phase2_endpoints.py; update Phase 2 docs at shared/docs/phase2_readme.md.

Current blockers:
- shared/openapi/phase2.yaml is locked by another agent; use phase2.yaml.v2 as the baseline; phase2.yaml.next/draft as staging artifacts if needed.

Artifacts to touch (when lock is released):
- shared/openapi/phase2.yaml (final surface; use v2 as source of truth)
- shared/server_api_v2.py
- shared/server_orchestrator.py
- shared/tests/api/test_phase2_endpoints.py
- shared/docs/phase2_readme.md

Coordination points:
- backend_dev: confirm runtime wiring and route registration for /v2 endpoints
- frontend_dev: validate Phase 2 surface compatibility with clients

Validation plan:
- Mirror Phase 1 patterns for LevelInput, RenderStats, Error components
- Add unit/integration tests scaffolding for endpoint presence and payload validation
- Include SSE event structure in tests if feasible

Delivery plan:
- When lock released, apply changes to phase2.yaml (prefer phase2.yaml.v2 as ground truth), run tests, and document results in phase2_readme.md.

End of handoff quick notes.