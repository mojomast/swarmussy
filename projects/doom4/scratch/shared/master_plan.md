# Master Plan – API Prototype Sprint

Vision
- Build a minimal, production-ready API prototype (Express) exposing editor state, plan, assets, levels, and entities with in-memory storage and optional disk persistence. Provide a clearly defined API contract, tests, CI integration, a frontend wiring path, and up-to-date documentation.

Scope
- Backend: Implement scratch/shared/infra/api-prototype/ Express server with endpoints for editor state, plan, assets, levels, entities, and world save/load; in-memory data store plus optional disk persistence; CORS; JSON schema validation; Supertest-based tests; TypeScript-first codebase with a parallel JS harness for tests if needed.
- Frontend: Initial wiring for Pixel McFrontend to consume /api/editor/state and /api/editor/plan; display and edit plan; basic error handling; minimal UI scaffolding.
- QA: Bugsy McTester to craft API contract tests; ensure alignment with server surface; add json schema validation tests; plan for end-to-end tests later.
- Deployment: Deployo McOps to extend CI/CD to run API contract tests; add npm scripts; document environment variables and workflow integration.
- Documentation: Docy McWriter to keep BUILD.md in-sync with API contracts, persistence rules, and testing guidance; add README_API_PERSISTENCE_TESTS.md with test guidance.

Goals & Deliverables
- A working Express-based API prototype under scratch/shared/infra/api-prototype/ with:
  - Endpoints: GET/POST for /api/editor/state, /api/editor/plan, /api/editor/assets, /api/editor/levels, /api/editor/entities, world save/load, health/version
  - In-memory store and simple disk persistence for world.json
  - JSON schema validation hooks (optional depending on dependency availability)
  - Basic tests using supertest to verify core endpoints
- A test harness and CI scaffolding to validate API contracts in CI
- Documentation updates and developer onboarding artifacts

Architecture Overview
- Layer 1: API surface (Express) – scratch/shared/infra/api-prototype/index.ts
- Layer 2: Persistence – in-memory models with optional disk persistence at data/world.json
- Layer 3: Contracts – align with scratch/shared/api_contracts.ts
- Layer 4: Testing – supertest-based tests under scratch/shared/infra/api-prototype/__tests__/
- Layer 5: CI/CD – npm scripts and GitHub Actions workflows to run API tests
- Layer 6: Frontend wiring – Pixel McFrontend to be wired to /api/editor/* in a progressive integration path

Milestones & Schedule
- Milestone 1: API prototype scaffold ready (endpoints + in-memory store) – Week 1
- Milestone 2: Disk persistence and basic tests added – Week 2
- Milestone 3: API contract tests aligned with server surface – Week 3
- Milestone 4: CI/CD integration for API tests – Week 4
- Milestone 5: Frontend wiring and docs updates – Week 5

Risks & Mitigations
- R1: Endpoint surface drift between server and tests. Mitigation: maintain a single source of truth in scratch/shared/api_contracts.ts and reference from tests.
- R2: JSON schema dependency availability in CI. Mitigation: make JSON schema usage optional with graceful fallback or vendor a lightweight validator.
- R3: Auth surface mismatch. Mitigation: start with AUTH_MODE disabled in dev; gate tests later when auth is implemented.
- R4: Disk persistence conflicts on concurrent writes. Mitigation: serialize writes and implement simple versioning for world.json.

Assumptions
- The team will operate within the designated scratch/shared workspace; code and docs live under scratch/shared.
- Endpoints will follow the naming convention /api/editor/* and health/version routes.
- CI will have Node.js 18+ runtime; tests can run without a full database.

Stakeholders
- Kyle (Product Owner) | Bossy McArchitect (Lead Architect) | Codey McBackend (Backend) | Pixel McFrontend (Frontend) | Bugsy McTester (QA) | Deployo McOps (CI/CD) | Docy McWriter (Documentation)

Governance & Communication
- Weekly syncs via plan dashboards; status updates to devplan.md at every milestone; blockers escalated in the Blockers & Risks section.
