# Dashboard Update Plan

- Status: 4 active tasks, 0 completed as of now.
- Next tasks: assign to Bugsy McTester for QA harness updates and cross-language test integration.
- Ensure GRID_API_BASE_URL gating logic is respected in CI harness and tests.
- Prepare scoped test suites for grid API, grid UI, and asset lifecycle.
- Coordinate with Codey and Pixel for API consistency and UI expectations.

Active tasks by Owner

Codey McBackend
- Finalize backend API readiness to support the new frontend profile features:
  - Ensure /users API endpoints are fully wired
  - Add/verify health checks
  - Provide an exportable contract doc for frontend integration
Status: In Progress

Pixel McFrontend 3
- Finalize frontend integration for the Doom Clone profile UI:
  - Connect ProfilePanel to app shell
  - Ensure doomBootstrapping emits doom-bootstrap-profile on load
  - Implement a simple README doc for localProfile usage
Status: In Progress

Bugsy McTester 2
- QA plan for local profile UI and backend user API:
  - Test Save/Load/Delete, auto-load, profile bootstrap, and API error cases (400/404/409)
  - Produce test results and a concise QA report
Status: In Progress

Docy McWriter
- Draft a user-facing README update that documents:
  - Local Doom Clone profile UI
  - Storage keys, data shape, bootstrapping flow
  - How to test locally
Status: In Progress

Completed
- Create user API (backend) and tests (already completed in prior tasks)
- Frontend Users.jsx and related QA/test artifacts (completed in prior steps)
- Local profile modules implemented (profile.js, ProfilePanel.jsx) and bootstrapping wired (completed)

Notes
- Swarm is actively executing across backend, frontend, QA, and docs tracks. Regular check-ins expected for blockers and risk mitigation.
