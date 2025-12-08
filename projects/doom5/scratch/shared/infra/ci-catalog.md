CI stub and dev-runtime catalog

- ci-stub.yml: GitHub Actions minimal workflow for tests/builds
- dev-runtime.Dockerfile: Dockerfile to run dev tooling locally
- ENV-VARS.md: guidance on environment variables and secrets

Usage:
- Use ci-stub.yml in .github/workflows
- Build image with docker build -f infra/dev-runtime.Dockerfile -t dev-runtime:latest .
