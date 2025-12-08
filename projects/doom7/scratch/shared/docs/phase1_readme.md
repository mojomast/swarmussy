# Phase 1 Consolidation — API and Backend Usage

This document describes Phase 1 pruning, updated contracts, and rollout guidance for Phase 1 consolidation. It mirrors the strategic direction outlined in the project master plan and development plan.

## Table of Contents
- [Overview](#overview)
- [Scope & Goals](#scope--goals)
- [API Usage: Updated Contracts](#api-usage-updated-contracts)
- [Backend Expectations](#backend-expectations)
- [UI/UX Changes](#uiux-changes)
- [Migration & Rollback](#migration--rollback)
- [Rollout Plan](#rollout-plan)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## Overview
Phase 1 focuses on pruning legacy contracts, consolidating engine routes, and stabilizing the Phase 1 data model. The changes are designed to simplify integration points for downstream services and reduce surface area for future migrations.

Key outcomes:
- Reduced API surface area via contract consolidation
- Clarified data contracts for Phase 1 data models
- Clear migration steps and rollback paths

> See master_plan.md and devplan.md for alignment with the broader program goals.

## Scope & Goals
- Remove deprecated Phase 0 contracts and consolidate remaining Phase 1 contracts
- Update API endpoints to reflect the new, stable contracts
- Update backend services to consume the new contracts
- Provide rollout and rollback procedures for production safety

## API Usage: Updated Contracts
The Phase 1 API surface is described in the OpenAPI spec under phase1.yaml. The primary runtime entry points are exposed behind the Phase 1 API Gateway.

- Discover available Phase 1 endpoints
  - Hitting the API root for Phase 1 will return a catalog of available resources

Example (curl):
```bash
export PHASE1_API_BASE="https://api.example.com/phase1"

curl -i "$PHASE1_API_BASE/health" \
  -H "Accept: application/json"
```

- Retrieve current Phase 1 contracts
```bash
curl -s "$PHASE1_API_BASE/contracts" | jq
```

- Trigger a Phase 1 migration task (see Migration section for preconditions)
```bash
curl -X POST "$PHASE1_API_BASE/migrate" \
  -H "Content-Type: application/json" \
  -d '{"target_version":"phase1.0.0"}'
```

> Full OpenAPI spec reference: phase1.yaml (see phase1_architecture.md for how to interpret contracts).

## Backend Expectations
Backends consuming Phase 1 contracts must:
- Validate input against the new Phase 1 contract schemas
- Persist changes using the Phase 1 migrations pipeline
- Emit structured events on a Phase 1 EventBus

## UI/UX Changes
The UI has been streamlined to present Phase 1 resources with a simplified flow:
- Phase 1 Overview page
- Phase 1 Contracts Explorer
- Phase 1 Migration Status Dashboard

Demo guidance and updated components are described in the frontend docs.

## Migration & Rollback
### Migration Steps
1. Ensure database migrations for Phase 1 have run (see MIGRATIONS.md).
2. Validate that all services are consuming Phase 1 contracts.
3. Switch traffic to Phase 1 endpoints behind a feature flag; monitor logs.
4. Run end-to-end tests; verify contract validations in staging.

### Rollback Plan
- If issues are observed, revert traffic to Phase 0 contracts and rollback DB migrations.
- Restore previous openapi phase contract version in API Gateway config.
- Repoint services to legacy endpoints and re-run tests.

## Rollout Plan
- Phase 1 pilot in staging (1 week) with synthetic data
- Incremental production rollout in 2 waves, paired with a health gate
- Finalize decommission of Phase 0 endpoints after verification

## Environment Variables
- PHASE1_API_BASE: Base URL for Phase 1 endpoints
- PHASE1_MIGRATIONS_DIR: Directory path for Phase 1 migration files
- PHASE1_CONTRACTS_PATH: Path to Phase 1 contract schemas
- PHASE1_DB_URL: Connection string for Phase 1 database
- PHASE1_LOG_LEVEL: Logging level (debug|info|warn|error)
- PHASE1_FEATURE_FLAGS: JSON map of feature flags (e.g., {"enablePhase1UI": true})

> These variables are read by the Phase 1 services at startup and can be overridden via deployment manifests.

## Troubleshooting
- If /health reports degraded state, check Phase 1 migrations and contract validation.
- Check OpenAPI phase1.yaml for endpoint deprecations or required fields.
- Confirm environment variables are loaded by each Phase 1 service.

## References
- Master plan: master_plan.md
- Development plan: devplan.md
- Phase 1 OpenAPI: phase1.yaml
- Phase 1 migrations: MIGRATIONS.md

