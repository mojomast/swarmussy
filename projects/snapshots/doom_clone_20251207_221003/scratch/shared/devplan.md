Doom Clone Dev Plan Dashboard

Overall Status: In Progress

Blockers & Risks
- ⚠ Canonical API surface and auth parity: Decide whether to enforce Bearer authentication in the backend API; will require test updates and gateway changes.
- ⚠ App shell readiness: Ensure the app shell is listening for doom-bootstrap-profile and can hydrate game state on startup.
- ⚠ CI/harness alignment: Consolidate cross-language tests and results into a single contract and dashboard.

Tasks by Owner

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
