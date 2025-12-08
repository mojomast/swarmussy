# Live Dev Plan Dashboard

Overall Status: Mixed progress. Active work across backend, frontend, QA, and CI tooling. See task owners below for current blockers and progress.

## Task ownership and progress
- Codey McBackend
  - [x] 52a20b9e - Create core ECS skeleton and render loop scaffolding (in progress -> updated later in UI)
  - [x] a18e9b85 - Continue with ECS core: finalize TypeScript components (completed)
  - [x] ab57a175 - ECS core scaffold (completed)

- Pixel McFrontend
  - [ ] 461e0b37 - Create a minimal UI shell for the game and in-engine editors (in_progress)
  - [ ] 6d7e46be - Level Editor UI wire-up to ECS bridge (in_progress)

- Bugsy McTester
  - [ ] ebf3448e - Define QA plan and safety checks (in_progress)
  - [ ] 75e728b1 - Draft/test cases for Level Editor UI integration and ECS rendering (in_progress)
  - [x] f78d18f3 - QA acceptance criteria (completed)

- Deployo McOps
  - [ ] 59ea76c8 - CI stub and packaging (in_progress)
  - [x] fe7fe8e4 - Build tooling (completed)
  - [ ] 3eb95698 - CI dev runtime Dockerfile (in_progress)

## Blockers & Risks
- ⚠️ CI workflow file missing (.github/workflows/ci-stub.yml) – needs to be added or configured.
- ⚠️ Level Editor integration relies on stable ECS bridge contracts; align data contracts before end-to-end tests.
- ⚠️ Security hardening and CI gating to be wired next.

