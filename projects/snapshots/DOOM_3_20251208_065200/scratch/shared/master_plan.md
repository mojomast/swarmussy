# Master Plan

## Doom-like Engine Integration
- The engine will be a lightweight, production-grade core designed to run in Node/TS with a tiny ECS and a tick loop. It will expose endpoints to fetch state and issue commands, enabling frontend integration and future engine features.

## Plan & Phases
1) Engine skeleton (ECS + tick loop) – backend
2) Level loading and basic world state representation
3) API surface for engine state and commands
4) Frontend integration wiring and renderer
5) Tests, CI, and docs

## Deliverables
- Engine core skeleton (ECS, tick loop) and in-memory world model
- API routes for engine state and commands
- Frontend API client and minimal renderer wiring
- Integration tests for engine endpoints and frontend hooks
- Documentation of engine API and usage

## Assumptions
- TypeScript-based modules living under scratch/shared/engine/
- Frontend will consume engine state via REST-like API
- Minimal rendering in frontend to visualize engine state

## Risks & Mitigations
- Risk: Engine API design changes; Mitigation: define stable contract early in this plan
- Risk: Coordination delay between backend and frontend; Mitigation: parallel workstreams with clear tasks

Plan ready. Say 'Go' to start execution.