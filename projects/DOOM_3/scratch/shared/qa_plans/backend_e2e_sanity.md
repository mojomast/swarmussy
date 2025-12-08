Backend E2E Sanity Plan
- Objective: Validate core endpoints health, level lifecycle, and player actions under a simple in-memory server.
- Scope: /api/health, /api/levels, /api/levels/load, /api/levels/save, /api/player/move, /api/player/shoot
- Approach: Spin up server, run a handful of sequential tests asserting success and proper validation errors.
- Security checks: verify basic auth header handling when enabled, verify rate-limiting for non-local IPs.
- Deliverables: test plan, test suite, and a short security report.
