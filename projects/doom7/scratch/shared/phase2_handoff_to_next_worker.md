Phase 2 OpenAPI Contract Extension - Handoff to Fresh Worker

Concise objective:
- Complete Phase 2 OpenAPI surface for engine controller and runtime data, aligned with Phase 1 patterns, under /v2/ endpoints.
- Ensure payloads, error formats, and schemas match Phase 1 conventions and wire into runtime (server_api_v2.py, server_orchestrator.py).

Current blockers:
- shared/openapi/phase2.yaml is locked by another agent (cannot edit). Use phase2.yaml.v2 as the reference anchor and apply changes when lock is released. Consider working on phase2.yaml.next/phase2.yaml.draft as staging artifacts if needed.

Target API surface (to be implemented once lock is released):
- GET /v2/editor/level
- POST /v2/editor/level
- GET /v2/engine/render_stats
- GET /v2/events/stream (Server-Sent Events)

Payloads and responses (align with Phase 1):
- Level (response): existing Level schema from Phase 1 "level.json" contract
- LevelInput (request): LevelInput schema, validates required fields for editing/creating a level
- RenderStats (response): keys mirroring Phase 1 runtime stats (e.g., frames_per_second, memory_usage, active_entities, etc.)
- Error (response): consistent error shape used in Phase 1 (code, message, details optional)
- SSE events (response): Event objects with type, timestamp, payload, etc. in a stable, forward-compatible shape

Artifacts to touch (blocked until lock release):
- shared/openapi/phase2.yaml
- shared/docs/phase2_readme.md
- shared/tests/api/test_phase2_endpoints.py
- shared/server_api_v2.py
- shared/server_orchestrator.py

What to verify with backend/frontend collaboration:
- backend_dev: Confirm that the /v2 surface matches runtime wiring expectations and that endpoints routes are registered in server_api_v2.py/server_orchestrator.py
- frontend_dev: Confirm that Phase 2 clients can consume the /v2 surface (levels, render_stats, and streaming events) with the same data shapes as Phase 1 equivalents

Planned validation approach:
- Mirror Phase 1 endpoint patterns for inputs/outputs and error handling
- Add OpenAPI component schemas for LevelInput, RenderStats, and Error that reuse Phase 1 assets where possible
- Create tests scaffolding in shared/tests/api/test_phase2_endpoints.py to verify endpoint presence and basic payload validation

Documentation touchpoints:
- Update shared/docs/phase2_readme.md with concrete endpoint examples and payload shapes once phase2.yaml is finalized

Notes for the handoff recipient:
- If clarifications are needed, open request_help with backend_dev and/or frontend_dev mentioning the exact surface and data contracts to validate compatibility.
- After lock release, prioritize updating phase2.yaml (prefer phase2.yaml.v2 as source of truth) and then synchronize docs/tests accordingly.

"End of handoff notes"