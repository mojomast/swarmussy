Phase 2 OpenAPI Contract Handoff — concise surface

Context
- Phase 2 OpenAPI contract integration: wire Phase 2 endpoints (engine controller, level editor, render_stats, events stream) into the runtime surface. Ensure parameter schemas, response schemas, and error formats align with Phase 1 contracts. Versioning via /v2 in the surface.
- Surface will land under the runtime surface (server_api_v2.py / server_orchestrator) with OpenAPI backing in shared/openapi/phase2.yaml (and subsequent phase2.yaml.* variants).

Proposed Phase 2 API surface (REST, /v2):
- Engine Controller (runtime orchestration)
  - POST /v2/engine/run
    - Description: Start an engine instance for a given scene/config
    - Request: { "scene_id": string, "config": object }
    - Response: { "engine_id": string, "status": "running" }
  - GET /v2/engine/{engine_id}/status
    - Description: Poll engine status and progress
    - Response: { "engine_id": string, "state": "idle|running|paused|stopped", "progress": number }
  - POST /v2/engine/{engine_id}/pause
    - Description: Pause engine
    - Response: { "engine_id": string, "status": "paused" }
  - POST /v2/engine/{engine_id}/stop
    - Description: Stop engine
    - Response: { "engine_id": string, "status": "stopped" }

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
  - GET /v2/events/stream
    - Description: Server-Sent Events stream for runtime events (engine status, editor events, etc.)

Key considerations
- Auth: Bearer token per endpoint
- Versioning: /v2 prefix; keep parity with Phase 1 contract naming conventions
- Error format: {"error": {"code": "<CODE>", "message": "<text>"}}
- Lists: support pagination via query params (limit, offset) where applicable
- Data models: reuse Phase 1 primitives where possible; Phase 2 adds engine/editor/render models in shared/schemas and shared/openapi/phase2.yaml
- Validation: align request/response schemas with Phase 1 contracts for consistency

Tests scaffolds (location and intent)
- Prepare contract tests at shared/tests/api/test_phase2_endpoints.py aligned to the above surface.
- Structure should cover: engine.run, engine.status, engine.pause/stop, editor level CRUD, editor export, render/stats fetch, and events/stream existence and basic behavior hooks.

Docs updates
- Update phase2_readme.md with a Contract surface section summarizing the endpoints, schemas, and versioning rules. Reference shared/openapi/phase2.yaml as the canonical contract source.

Next steps for the team
- Backend glue to wire OpenAPI phase2.yaml into runtime surface and ensure endpoint handlers exist in server_api_v2.py/server_orchestrator.
- Coordinate with frontend for UI mappings against /v2 surface and data shapes.
- Create actual contract tests scaffolds in shared/tests/api/test_phase2_endpoints.py.

Owner notes
- Primary: backend_dev (API wiring), api_designer (OpenAPI surface)
- Secondary: frontend_dev (UI alignment)

Acceptance criteria
- Phase 2 endpoints surface is wired in runtime, with /v2 namespace, and ready for integration tests.
- Phase 2 docs reflect contract surface and endpoint shapes.
- Tests scaffolds exist and are ready to be implemented.
