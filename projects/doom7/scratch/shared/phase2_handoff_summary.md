Phase 2 OpenAPI contract handoff (concise surface)

Goal
- Wire Phase 2 OpenAPI surface into the runtime API layer under /v2 and align with Phase 1 contracts.

Key Endpoints Surface (under /v2)
- Engine Controller
  - POST /v2/engine/run
  - GET /v2/engine/{engine_id}/status
  - POST /v2/engine/{engine_id}/pause
  - POST /v2/engine/{engine_id}/stop
- Level Editor (runtime surface)
  - GET /v2/editor/levels
  - POST /v2/editor/levels
  - GET /v2/editor/levels/{level_id}
  - PUT /v2/editor/levels/{level_id}
  - DELETE /v2/editor/levels/{level_id}
  - POST /v2/editor/levels/{level_id}/export
- Render Stats
  - GET /v2/render/stats
  - GET /v2/render/stats/summary
- Events Stream
  - GET /v2/events/stream (Server-Sent Events)

Runtime wiring touchpoints
- Python runtime surface files: server_api_v2.py, server_orchestrator.py, and any endpoint glue under engine/ as needed.
- OpenAPI backing: shared/openapi/phase2.yaml (canonical contract) and phase2.yaml.next/v2 variants as needed.

Tests scaffolds
- Create contract tests at shared/tests/api/test_phase2_endpoints.py covering the full surface (engine.run, engine.status, engine.pause, engine.stop, editor CRUD, render stats, events stream).
- Use integration style tests against the in-process runtime surface or a test server wired to server_api_v2.py.

Docs
- Update phase2_readme.md with the contract surface summary and versioning rules.

Next steps for the fresh worker
- Implement and wire the endpoints as per above surface.
- Ensure parameter schemas, response schemas, and error formats align with Phase 1 contracts.
- Add auth requirements per endpoint and ensure consistent error payloads.
- Create/adjust contract tests scaffolds in shared/tests/api/test_phase2_endpoints.py.
- Update phase2_readme.md and phase2.yaml references in docs.
