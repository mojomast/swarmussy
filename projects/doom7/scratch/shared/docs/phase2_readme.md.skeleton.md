# Phase 2 Quickstart and Runbook (Skeleton)

This document outlines a skeleton for Phase 2 Quickstart and Runbook. It is intended as a living draft to accelerate documentation while the Phase 2 API surface and runtime are evolving.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Startup & Run](#startup--run)
- [Authentication](#authentication)
- [API Surface (Phase 2)](#api-surface-phase-2)
- [Observability & Telemetry](#observability--telemetry)
- [Health Checks](#health-checks)
- [Troubleshooting](#troubleshooting)
- [Cross-References](#cross-references)
- [Diagrams](#diagrams)

## Overview
Phase 2 Quickstart and Runbook for operators, developers, and on-call engineers. This skeleton organizes the surface and points to the canonical OpenAPI contract and runtime references.

## Prerequisites
- Access to Phase 2 API surface (openapi/phase2.yaml)
- Access to authentication provider (OAuth2 / JWT)
- Environment configured for Phase 2 base URL

## Environment Variables
- PHASE2_BASE_URL: Base URL for Phase 2 API (e.g., https://api.example.com/v2)
- PHASE2_AUTH_PROVIDER: OAuth2 provider (e.g., auth.example.com)
- PHASE2_CLIENT_ID: OAuth2 client ID
- PHASE2_CLIENT_SECRET: OAuth2 client secret (securely stored)
- PHASE2_LOG_LEVEL: Logging level (debug|info|warn|error)
- PHASE2_TLS_CERT_PATH: Path to TLS client certs (if mutual TLS is required)
- PHASE2_FEATURE_FLAGS: Comma-separated feature flags (e.g., world-preview, engine-v2)

## Startup & Run
- Typical startup steps for local/dev environment (placeholder)
- How to run the Phase 2 services (e.g., start gateway, orchestrator, engine plugins) using your orchestrator
- How to verify status pages and API surface after startup

## Authentication
- How to obtain an access token from the configured provider
- How to attach Authorization: Bearer <token> to Phase 2 requests
- Token expiry handling and refresh flow

## API Surface (Phase 2)
- Refer to the canonical OpenAPI contract for Phase 2: shared/openapi/phase2.yaml
- Endpoint families (examples, placeholders):
  - /v2/auth/login
  - /v2/worlds
  - /v2/runtimes
  - /v2/engine
  - /v2/events
- Request/response conventions (schema usage, error formats)
- Example payloads to illustrate common operations (placeholder content)

## Observability & Telemetry
- Metrics exposed by the API and orchestrator
- Logs and traces (e.g., OpenTelemetry compatibility)
- Health endpoints and readiness checks

## Health Checks
- Endpoint health checks and how to assertion in runbooks
- Basic sanity checks for Phase 2 components

## Troubleshooting
- Common issues and initial steps
- How to collect logs and reproduce failures
- Contact points for escalation

## Cross-References
- Phase 2 Architecture: scratch/shared/docs/phase2_architecture.md
- Phase 2 Rollout: scratch/shared/docs/phase2_rollout.md
- Phase 2 API surface: scratch/shared/openapi/phase2.yaml
- Master plan: scratch/shared/docs/master_plan.md

## Diagrams
```
flow
  title Phase 2 Quickstart and Runbook (Skeleton)
  A[Gateway] --> B[Orchestrator]
  B --> C[Engine Plugins]
  C --> D[Event Bus]
  D --> E[Data Store]
```

Note: This skeleton should be replaced with finalized content before release.