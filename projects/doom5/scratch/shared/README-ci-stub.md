CI Stub and Dev Runtime

Overview
- Minimal GitHub Actions workflow that runs ECS unit tests scaffolding and UI scaffold tests via a small CI script.
- A dev runtime Dockerfile.dev is provided to simulate a runtime environment for local testing.

What I added
- .github/workflows/ci-stub.yml: Triggers on push/PR to main/master; runs ci-run.sh.
- scripts/ci-run.sh: Lightweight orchestration to run npm scripts if present and to build artifacts when available.
- infra/Dockerfile.dev: Node-based dev runtime that can run ci-run.sh inside container.

Local development and testing
- Ensure you have Node.js installed locally (v18+).
- Run locally:
  - npm install (if needed by your project)
  - bash scratch/shared/scripts/ci-run.sh
- Build frontend/backend if scripts exist:
  - npm run build, npm run build:frontend, npm run build:backend

Environment variables and secrets
- The CI stub does not require any secrets by default.
- If your project uses environment variables, provide them via a .env file and ensure tests/scripts read from process.env.
- Do not commit secrets; use GitHub Secrets in the real workflow.

Extending the CI stub
- Add new npm scripts in package.json (e.g., test-ui, build:frontend) to be picked up by ci-run.sh.
- Add extra steps to ci-run.sh for linting, type checking, or end-to-end UI tests as needed.
