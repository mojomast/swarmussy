CI/CD and deployment plan for Levels Admin API

Overview
- This repository contains a ready-to-run Level API (Express) with seed data initialization and a Docker-based CI/CD pipeline triggered by GitHub Actions.

What runs in CI
- TypeScript compile using tsc
- Unit/validation tests (where present)
- Build Level API Docker image (Dockerfile.level_api)
- Save artifact for downstream steps

What runs in CD (optional)
- Deploy to a registry (Docker Hub or ECR) from GH Actions
- Deploy to Kubernetes or a VM via terraform/helm (not included in this repo by default)

Environment variables and secrets
- Local/dev env vars (via a .env or docker-compose):
  - API_BASE_URL=http://localhost:3000
  - PORT=3000
- Production/CI secrets (to be configured in GH Actions or your CI):
  - DOCKERHUB_USERNAME
  - DOCKERHUB_PASSWORD
  - DOCKER_REGISTRY (e.g., docker.io or your private registry)
  - REGISTRY_NAMESPACE
  - REGISTRY_REPOSITORY

How to run locally
- Install dependencies: cd scratch/shared && npm ci
- Build: cd scratch/shared && npm run build
- Run API with seed: node dist/server.js (or via Docker Compose)
- If using Docker: docker-compose -f docker-compose.yml up --build

Docker Compose (local dev)
- scratch/shared/docker-compose.yml defines:
  - level-api: builds from Dockerfile.level_api, exposes 3000
  - ui: placeholder container

Notes
- Seed data runs on startup via server.ts calling seedFromData(sampleLevels)
- Migrations are not implemented in this sample; extend server startup to run migrations if needed.
