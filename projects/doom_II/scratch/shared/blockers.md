## Active Blockers

- ⚠️ Level API PUT /levels/:id integration
  - What: PUT endpoint implemented and tested in TS/JS variants; some tests pass but integration with the in-repo test harness is ongoing.
  - Who: Codey McBackend 4 / 937f7222-c3f3-468b-919b-b9ca8bef19a4 (PUT work owner)
  - What’s needed: final review and merge plan, and a full end-to-end test pass in CI.
  - Impact: Prevents complete stabilization of Level API; clearing this will unblock final API surface.

- ⚠️ Devplan refresh required
  - What: Bossy McArchitect to refresh scratch/shared/devplan.md to reflect the updated scope (CI, UI, API expansions).
  - Who: Bossy McArchitect
  - What’s needed: approval to regenerate the dev dashboard so the team aligns on milestones.

- ⚠️ UI PUT wiring for Level admin
  - What: Levels Admin UI currently lists/edits via PUT is prepared but not wired to the API; require wiring in frontend to call PUT /levels/:id and handle responses.
  - Who: Pixel McFrontend 2 / 013470f4-0196-44af-8d49-661b07f29905
  - What’s needed: implement fetch/axios call for update and test end-to-end with API.

- ⚠️ CI/CD artifact parity
  - What: CI currently builds Docker image and tests; ensure parity with local Dockerfile naming and image tagging.
  - Who: Deployo McOps 2 / 5040e54c-7237-41b4-bf06-4a6c52987ca3
  - What’s needed: finalize naming and registry flows if we push to a central registry.

- ⚠️ UI testing scaffolding alignment
  - What: Tests for Levels Admin UI are not yet wired to API; Add UI-end-to-end tests or mocks.
  - Who: Pixel McFrontend 2 / 013470f4-0196-44af-8d49-661b07f29905
  - What’s needed: end-to-end tests using Playwright/Cypress or a lightweight in-browser test harness.

If blockers are resolved, we will proceed with finalizing PUT API integration, merge to main, refresh devplan, and push through CI readiness.
