CI/CD Build Configuration and Targets

Overview
- Lightweight, cross-platform setup using Vite (for dev server) and ESBuild (for production bundling).
- NPM scripts expose: dev (dev server), build (production bundle), test (stub).
- Minimal CI stubs suitable for GitHub Actions, GitLab CI, or Jenkins.

Build Targets
- dev: Start Vite dev server with TS support.
- build: Produce a production bundle with ESBuild.
- test: Placeholder for CI test script (no external dependencies).

Environment Variables
- VITE_DEV_HOST: Host for the dev server (default: 0.0.0.0)
- VITE_DEV_PORT: Port for the dev server (default: 5173)
- ENTRY: Path to the TypeScript entry file (default: src/main.ts)
- BUILD_OUT: Output directory for production bundle (default: dist)
- CI: Flag indicating CI environment (e.g., true/false)

File Molders and Entry Points
- shared/vite.config.ts: Vite config for TS projects (no framework plugins by default).
- scratch/shared/scripts/dev.ts: Dev server bootstrap using Vite's programmatic API.
- scratch/shared/scripts/build.ts: Production build via ESBuild.
- package.json: Scripts: dev, build, test.

CI Stub Guidelines
- CI should install dependencies, run npm ci, and execute npm run build.
- Optional: npm run test (if tests are added).
- Cache node_modules where appropriate for speed.

Notes
- This scaffold is intentionally minimal to avoid heavy tooling.
- Secrets are not committed; use environment variables or CI secrets.
