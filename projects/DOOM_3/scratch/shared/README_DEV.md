Acknowledged. Plan: update CI/CD to support repository-backed API layer, ensure unit tests run on PRs, adjust docker-compose and deployment manifests to accommodate repository-pluggable API, and refresh local dev docs.

Files to touch:
- GitHub Actions: pr-ci.yml (repo-backed API tests), possibly adjust cleanup-ci.yml and pr-ci.yml
- Docker/Compose: cleanup/app Dockerfile, start_api.sh supports repo URL, compose files
- Deployment manifests: k8s cleanup deployment.yaml, etc.
- Local dev docs: README_DEV and infra/dev guide.

Environment variables and secrets:
- REPO_API_URL (repo URL of API layer)
- REPO_API_BRANCH
- DB host/port if using local DB in cleanup app
- For k8s: IMAGE tags, container registry credentials

Acceptance criteria:
- PRs run unit tests against repository-backed API layer
- Local dev docs refreshed
- Repo-plug API is exercised via start_api.sh in container
