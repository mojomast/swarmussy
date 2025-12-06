# Blockers and Ownership

Status: Go-callback: Cadence locked; Go signal issued

Blocker 1: Standup scheduling alignment and owner assignment
- Description: Cadence locked; daily standup at 09:00 UTC, 15 minutes
- Owner: Checky McManager
- Rationale: Synchronize across Auth, Wallet, Shop, Games, and Infra work
- Resolution criteria: Cadence present in status_report and blockers updated accordingly

Blocker 2: API contracts alignment across per-service modules (auth, wallet, shop, games)
- Description: Matrix published; cross-service alignment finalized
- Owners: Auth Lead, Wallet Lead, Shop Lead, Games Lead
- Rationale: Prevent mid-sprint contract churn that breaks QA harness
- Resolution criteria: Finalized contract matrix published under scratch/shared/docs/api_contracts.md

Blocker 3: CI/CD gating and live Dev Plan integration
- Description: Gate readiness of dashboards and artifact integration in CI/CD pipelines.
- Owner: Deployo McOps
- Rationale: Ensure end-to-end automation before Go
- Resolution criteria: CI gates exist, basic pipelines wired, dashboards update health checks

Blocker 4: Inter-service authentication wiring
- Description: Ensure JWT generation, validation, and propagation across services.
- Owner: Bossy McArchitect
- Rationale: Security and access control across modules
- Resolution criteria: Token lifecycle defined, middleware implemented consistently, test coverage in QA harness

Next steps
- Monitor blockers and progress; close blockers as Go prepares per-service scaffolding
- Publish the final API contract matrix and onboarding README for auth scaffolding
- Ensure Dev Plan reflects blockers and decision points

Notes
- Update blockers.md as blockers are resolved and new blockers arise.
Blocker 5: JWT enforcement on protected routes
- Description: Wire and enforce Authorization: Bearer <token> on protected endpoints; update auth endpoints to use bcrypt + JWT; QA harness extended with 401/403 tests
- Owner: Bossy McArchitect
- Rationale: Security hardening across modular backend
- Resolution criteria: JWT middleware wired on /api/wallet/*, /api/shop/*, /api/games/*; /api/auth/register/login use bcrypt+JWT; QA harness tests cover 401/403 paths
