# Decisions Log

- API Contracts Lock: Pending Bossy approval to lock LevelData payload schema for load/save to prevent typing drift.
- Auth Middleware: Decision pending; propose a toggleable middleware to support test parity and production features.
- Router Interface: Await Bossy direction on Express-like Router shape and middleware semantics.
- Engine Tick Strategy: Agree on a gravity-like deterministic tick for testability; hooks for additional systems to be added (movement, collision).
- CI Strategy: Propose lightweight CI config to validate unit/integration tests; more details to follow once router/API decisions are locked.
