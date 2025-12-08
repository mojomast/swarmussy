API Persistence QA Plan - Execution Guide
--------------------------------------
- Prereqs: Node.js, npm, TypeScript, jest or ts-node (CI matrix should cover Node/TS)
- Environment vars: API_BASE_URL, API_AUTH_TOKEN(optional), AUTH_ENABLED(optional)
- Run: npm test (or yarn test) in shared/ with TS/Jest setup
- End-to-end: HTTP integration tests exercise /api/editor/state, /api/editor/plan, /api/editor/assets, /api/world/save/load
- Notes: Tests assume JSON payloads per /api/editor/* contracts; adapt as backend contract evolves
- CI: Add a matrix for Node/TS to mirror API behavior; ensure tests run under both Linux and Windows runners
