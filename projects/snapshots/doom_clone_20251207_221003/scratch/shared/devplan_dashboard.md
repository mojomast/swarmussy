Doom Clone Dev Plan Dashboard

Status: In Progress

Blockers & Risks
- Canonical API surface and auth parity: Decide whether to enforce Bearer authentication in API. Needs human guidance.
- App shell readiness: Ensure the app shell is listening for doom-bootstrap-profile and can hydrate game state on startup.
- CI/harness alignment: Consolidate cross-language tests and results into a single contract and dashboard.

Current Tasks by Owner
- Codey McBackend
  - EngineCore integration: bridge EngineCore with app shell and API contracts; add integration test scaffolding.
  - Status: Planned
- Pixel McFrontend 3
  - DoomShell wiring: ensure app shell consumes doom-bootstrap-profile event; render ProfilePanel; commit frontend integration notes.
  - Status: Planned
- Bugsy McTester 2
  - QA plan for cross-language parity: expand tests to 400/404/409; create crosslang QA doc.
  - Status: Planned
- Docy McWriter
  - Documentation updates: finalize cross-link docs and overall dev plan appendix.
  - Status: Planned

Milestones: 
- Backend/frontend contracts finalized
- Bootstrapping wired into app shell
- QA cross-language plan validated

Plan updated. Awaiting 'Go' to start execution.