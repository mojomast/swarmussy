# Dev Plan Dashboard

- Overall Status: Planning - awaiting Go

## Sprint Goals
- Build a production-ready API prototype (Express) exposing editor state, plan, assets, levels, and entities with in-memory storage and optional disk persistence. Provide a clearly defined API contract, tests, CI integration, frontend wiring path, and up-to-date documentation.

## Tasks & Owners
- **Codey McBackend**
  - Implement API prototype scaffolding under scratch/shared/infra/api-prototype/ with Express, endpoints for editor state, plan, assets, levels, entities, world save/load; in-memory store; JSON schema validation hooks; CORS; basic tests via supertest.
- **Pixel McFrontend**
  - Create initial UI wiring to /api/editor/state and /api/editor/plan; plan editor UI; basic error handling; scaffolding for future asset/level/entity wiring.
- **Bugsy McTester**
  - Define and implement API contract tests; ensure alignment with server surface; add JSON schema validation tests; plan end-to-end tests later.
- **Deployo McOps**
  - Extend CI/CD to run API contract tests; add npm script (e.g., npm run test:api); finalize env docs and test matrices in CI.
- **Docy McWriter**
  - Update BUILD.md and README_API_PERSISTENCE_TESTS.md with API contracts, schemas, persistence rules, and testing guidance; add Mermaids diagrams if needed.
- **Checky McManager**
  - Track progress; keep devplan.md in sync; report blockers; coordinate cross-team alignment.

## Blockers & Risks
- ⚠️ Server surface drift between server.ts and API prototype tests; require contract freeze or mapping.
- ⚠️ JSON schema dependency availability in CI; need a fallback strategy.
- ⚠️ Auth gating differences between development and production; plan to toggle in dev.

## Milestones
- M1: API prototype scaffold ready – Endpoints + in-memory store
- M2: Disk persistence + basic tests
- M3: API contract tests aligned with server surface
- M4: CI/CD integration for API tests
- M5: Frontend wiring and docs updates

## Notes
- All work lives under scratch/shared. Keep the master plan as the single source of truth for scope and owners.
