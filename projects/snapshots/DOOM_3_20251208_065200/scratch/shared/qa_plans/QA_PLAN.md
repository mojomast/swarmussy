# QA Plan - Backend/Frontend Integration Tests

Updated for concrete integration tests and frontend API hooks.

Test objectives:
- Validate backend endpoints health, level load/save, player move/shoot, inventory.
- Validate frontend API wrappers and their effect on UI state via mocked fetch.
- Ensure tests are isolated and deterministic across runs.

Test scope:
- Backend: /api/health, /api/levels, /api/levels/:id, /api/levels/load, /api/levels/save, /api/player/move, /api/player/shoot, /api/inventory
- Frontend: fetch wrappers in shared/src/api.ts, UI state updates in tests

Test approach:
- Use in-memory Express server (shared/server.ts) for integration tests
- Unit tests for core logic in shared/tests/core_api.test.ts (existing)
- Integration tests for API endpoints in shared/tests/integration_backend_endpoints.test.ts (existing)
- Frontend API wrappers tested via shared/tests/integration_fetch_wrappers.test.ts and shared/tests/integration_frontend_api.test.ts (added)

Risks & mitigations:
- Risk: flaky tests due to shared state. Mitigation: resetMemoryStore and per-test isolations.
- Risk: mismatch between client/server types. Mitigation: Use shared/src/api.ts contracts across client & server tests.
- Risk: network-like timing in E2E. Mitigation: deterministic mocks and short timeouts.

Success criteria:
- All integration tests pass with 200 responses and expected payloads.
- QA plan coverage aligns with requirements.
