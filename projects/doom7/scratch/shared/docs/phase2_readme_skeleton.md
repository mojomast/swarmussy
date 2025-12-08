# Phase 2 Readme (Skeleton)

Table of Contents
- [Overview](#overview)
- [OpenAPI surface alignment](#openapi-surface-alignment)
- [Getting started](#getting-started)
- [Environment variables](#environment-variables)
- [Endpoints overview](#endpoints-overview)
- [Auth & security](#auth-security)
- [Request/response conventions](#requestresponse-conventions)
- [Payload samples](#payload-samples)
- [Error handling](#error-handling)
- [Cross-references](#cross-references)
- [Troubleshooting](#troubleshooting)
- [Glossary](#glossary)
- [References](#references)

---

## Overview
Phase 2 introduces a new API surface at /v2. This skeleton anchors to the OpenAPI contract at shared/openapi/phase2.yaml and provides a structure for getting started and cross-references.

---

## OpenAPI surface alignment
- Base path: /v2
- Authentication/authorization mechanisms to be described per phase2.yaml
- Endpoints mapping to gateway/orchestrator/engine components
- Error envelopes aligned with phase2.yaml
- Cross-references to the Phase 2 contract at `shared/openapi/phase2.yaml`

Note: The canonical endpoint list should be extracted from phase2.yaml and populated here as a living reference.

---

## Getting started
- Prerequisites: tooling, access token, base URL
- How to invoke the API (curl/example client)

```bash
export BASE_URL=https://api.example.com/v2
export TOKEN=...
curl -H "Authorization: Bearer $TOKEN" $BASE_URL/engine/render -d '{"input":"sample"}'
```

---

## Environment variables
- API_BASE_URL
- API_TOKEN_URL
- API_CLIENT_ID
- API_CLIENT_SECRET
- LOG_LEVEL

---

## Endpoints overview
- POST /engine/render
- GET /engine/status
- GET /events/stream
- ... (extract from phase2.yaml for full list)

---

## Auth & security
- OAuth2 / JWT tokens, scopes, expiration
- Token rotation strategies
- Audit logging and secure storage

---

## Request/response conventions
- JSON payloads
- Standard error envelope
- Idempotency keys and retry headers

---

## Payload samples
- Placeholder payloads to be filled after the Phase 2 contract stabilization

---

## Error handling
- Error codes and messages (structure per phase2.yaml)

---

## Cross-references
- Phase 2 OpenAPI contract: `shared/openapi/phase2.yaml`
- Phase 1: `shared/openapi/phase1.yaml` (compat shims)
- Master Plan: `shared/docs/master_plan.md`

---

## Troubleshooting
- Common issues and remediation steps

---

## Glossary
- Phase 2 terms and acronyms

---

## References
- Phase 2 OpenAPI contract: `shared/openapi/phase2.yaml`
- Phase 2 next-gen draft: `shared/openapi/phase2.yaml.next` (for reference)
