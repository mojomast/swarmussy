# Dev Plan

- Overall Status: Pending start
- Plan owner: Bossy McArchitect

## Objectives
- Build a small Doom-like engine core integrated with the existing backend and front-end shells.
- Provide a stable API for engine state and commands.
- Wire frontend to fetch engine state and render a minimal scene.

## Tasks & Owners
- Codey McBackend: Create engine core (scratch/shared/engine/), provide TS interfaces and test scaffolding.
- Pixel McFrontend: Create minimal UI to display engine state and a mock render, wire to engine API.
- Docy McWriter: Document engine API and usage in scratch/shared/engine/README.md.
- Bugsy McTester: Define QA plan and write tests for engine core behavior.

- Blockers & Risks: TBD

---

<!-- LIVE_DASHBOARD_START -->

## Live Task Dashboard

### Overall Status

- Active agents: 21
- Total tasks: 29
  - Pending: 0
  - In Progress: 21
  - Completed: 8
  - Failed: 0

### Tasks by Agent

#### Bugsy McTester
- [x] ✅ (308d386a) Set up initial QA plan and environment: - Define baseline test plan for backend and frontend - Create a basic test su...
- [ ] 🔄 (f3143201) Plan concrete QA tasks for frontend-backend integration: - Update QA plan to cover integration tests, API contract va...
- [ ] 🔄 (b4af7c73) Plan the next QA batch: - Objective: Expand unit tests for backend endpoints and frontend API integrations; add basic...
- [x] ✅ (453c8af8) Execute QA batch: Build integration tests for backend endpoints and frontend API hooks: - Add integration tests for h...

#### Bugsy McTester 3
- [ ] 🔄 (9b1823ee) Plan the QA batch for engine integration: create tests for Engine core (start/stop/tick), ensure integration with bac...
- [ ] 🔄 (b07bd954) QA batch for engine integration: Create tests for Engine core (start/stop/tick), ensure integration with backend worl...

#### Codey McBackend
- [x] ✅ (4361b467) Plan and implement the core backend API scaffold for the project: - Files to create/modify under scratch/shared/ for ...
- [ ] 🔄 (d5d3e19e) Plan the next concrete backend batch: - Objective: Implement a small, production-ready backend feature set tied to th...
- [ ] 🔄 (baa5763e) Plan the next concrete backend batch: - Objective: Implement a production-ready feature set anchored to the current A...
- [x] ✅ (de0dece5) Execute backend batch: Implement an Express-like router, endpoints, and in-memory store enhancements: - Create a simp...

#### Codey McBackend 10
- [ ] 🔄 (5c7d99b7) Prepare to assist with engine task after core engine scaffold is drafted; ensure alignment with backend store and tests.

#### Codey McBackend 11
- [ ] 🔄 (115560c0) Plan the concrete engine batch: design Engine core, data models, and integration hooks with scratch/shared/server.ts....
- [ ] 🔄 (ec5a075e) Engine batch: Implement core Engine skeleton under scratch/shared/engine.ts. - Deliverables:   - Engine class with st...

#### Codey McBackend 12
- [ ] 🔄 (76e2f777) Plan the concrete engine batch: extend in-memory engine hooks to support a Doom-like engine loop; outline and wire En...
- [ ] 🔄 (11efef67) Engine batch: Create a precise Engine interface and a gravity-like tick. Provide an Engine class skeleton in scratch/...

#### Codey McBackend 2
- [x] ✅ (9dbefd7c) Plan next concrete batch: frontend-backend integration pass. Tasks: - Wire frontend /api calls to backend endpoints i...

#### Codey McBackend 3
- [x] ✅ (501730b3) Frontend-Backend Integration Batch: Implement a concrete backend integration batch. - Extend in-memory API router to ...

#### Codey McBackend 4
- [ ] 🔄 (bda1888d) Execute: Implement production-grade engine core and Doom-like mechanics scaffold. Build a minimal engine loop that in...
- [ ] 🔄 (d11dfb6a) Plan engine integration: Create scratch/shared/engine.ts with Engine class, provider interfaces, and a plug-in step p...

#### Codey McBackend 6
- [ ] 🔄 (4ef8c5f8) Plan and execute a production-grade engine batch for the Doom clone: - Objective: Build a minimal, instanceable engin...
- [ ] 🔄 (31895ad8) Plan & execute production-grade engine batch: Build a minimal ECS-based engine core with a few systems (Movement, Col...

#### Codey McBackend 7
- [ ] 🔄 (0b0b3467) Plan the next concrete backend batch: Engine core integration scaffold to support a Doom-like engine loop. Deliverabl...

#### Codey McBackend 8
- [ ] 🔄 (1c085455) Execute backend batch: Implement production-grade engine core and Doom-like engine scaffold. - Files to create: scrat...

#### Codey McBackend 9
- [ ] 🔄 (bed8d125) Awaiting engine task input; prepare to assist with engine integration if needed (offer review and co-implementation s...

#### Pixel McFrontend
- [x] ✅ (55ed33f3) Plan and implement the frontend scaffolding: - Create React components scaffold, basic routes, and a canvas viewer - ...
- [ ] 🔄 (583db3f0) Plan concrete frontend-backend integration tasks: - Update src/api.ts to strongly type endpoints and ensure calls mat...
- [ ] 🔄 (90665d75) Plan the next concrete frontend batch: - Objective: Integrate frontend with backend endpoints; add a minimal UI for /...
- [x] ✅ (aa531ba0) Execute frontend batch: Integrate with backend endpoints and establish a minimal LevelEditor flow: - Add API wrappers...

#### Pixel McFrontend 3
- [ ] 🔄 (be7ca851) Plan the next concrete frontend batch: wire Engine/World hooks into UI; add a minimal LevelEditor flow showing a mock...

### Blockers & Risks

- None currently recorded. If something is blocked, describe it here so the human can help.
